"""Django signal handlers for admin."""

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import gettext as _

import django_rq

from modoboa.core import models as core_models, signals as core_signals
from modoboa.lib import exceptions, permissions, signals as lib_signals
from modoboa.lib.email_utils import split_mailbox
from modoboa.parameters import tools as param_tools
from . import lib, models, postfix_maps, signals as admin_signals


@receiver(signals.post_save, sender=models.Domain)
def update_domain_mxs_and_mailboxes(sender, instance, **kwargs):
    """Update associated MXs and mailboxes."""
    if kwargs.get("created"):
        return
    instance.mailbox_set.filter(use_domain_quota=True).update(
        quota=instance.default_mailbox_quota
    )
    if instance.old_mail_homes is None:
        return
    qset = models.Quota.objects.filter(username__contains=f"@{instance.oldname}")
    for q in qset:
        username = q.username.replace(f"@{instance.oldname}", f"@{instance.name}")
        models.Quota.objects.create(
            username=username, bytes=q.bytes, messages=q.messages
        )
        q.delete()
    for mb in instance.mailbox_set.all():
        mb.rename_dir(instance.old_mail_homes[mb.pk])
    # FIXME: could be replaced by
    # .update(address=Concat("local_part", Value(instance.name)))
    # if the local_part was stored aside the address...
    for alias in instance.alias_set.all():
        alias.address = "{}@{}".format(alias.address.split("@", 1)[0], instance.name)
        alias.save(update_fields=["address"])


@receiver(signals.post_save, sender=models.Domain)
def create_dkim_key(sender, instance, **kwargs):
    if not instance.enable_dkim:
        return
    queue = django_rq.get_queue("dkim")
    queue.enqueue(call_command, "modo", "manage_dkim_keys", f"--domain={instance.name}")


@receiver(signals.post_save, sender=models.DomainAlias)
def create_alias_for_domainalias(sender, instance, **kwargs):
    """Create a dedicated alias for domain alias."""
    if not kwargs.get("created"):
        return
    alias = models.Alias.objects.create(
        address=f"@{instance.name}", enabled=True, internal=True
    )
    models.AliasRecipient.objects.create(
        address=f"@{instance.target.name}", alias=alias
    )


@receiver(signals.post_delete, sender=models.DomainAlias)
def remove_alias_for_domainalias(sender, instance, **kwargs):
    """Remove the alias associated to domain alias."""
    models.Alias.objects.filter(address=f"@{instance.name}").delete()


@receiver(signals.post_save, sender=models.Mailbox)
def manage_alias_for_mailbox(sender, instance, **kwargs):
    """Create or update a "self alias" for mailbox (catchall)."""
    if kwargs.get("created"):
        alias, created = models.Alias.objects.get_or_create(
            address=instance.full_address,
            domain=instance.domain,
            internal=True,
            defaults={"enabled": instance.user.enabled},
        )
        models.AliasRecipient.objects.create(
            address=instance.full_address, alias=alias, r_mailbox=instance
        )
        return
    old_address = getattr(instance, "old_full_address", None)
    if old_address is None or old_address == instance.full_address:
        return
    # Update old self alias
    alr = models.AliasRecipient.objects.get(
        alias__address=old_address,
        address=old_address,
        r_mailbox=instance,
        alias__internal=True,
    )
    alr.address = instance.full_address
    alr.save()
    alr.alias.address = instance.full_address
    alr.alias.domain = instance.domain
    alr.alias.save()

    # Update AliasRecipient instances
    instance.aliasrecipient_set.filter(alias__internal=False).update(
        address=instance.full_address
    )


@receiver(signals.pre_delete, sender=models.Mailbox)
def mailbox_deleted_handler(sender, **kwargs):
    """``Mailbox`` pre_delete signal receiver.

    In order to properly handle deletions (ie. we don't want to leave
    orphan records into the db), we define this custom receiver.

    It manually removes the mailbox from the aliases it is linked to
    and then remove all empty aliases.
    """
    from modoboa.lib.permissions import ungrant_access_to_object

    mb = kwargs["instance"]
    ungrant_access_to_object(mb)
    for ralias in mb.aliasrecipient_set.select_related("alias"):
        alias = ralias.alias
        ralias.delete()
        if not alias.aliasrecipient_set.exists():
            alias.delete()
    models.Quota.objects.filter(username=mb.full_address).delete()
    request = lib_signals.get_request()
    if request:
        if not request.localconfig.parameters.get_value(
            "handle_mailboxes", raise_exception=False
        ):
            return
        keepdir = request.POST.get("keepdir", "false") == "true"
        if keepdir:
            return
        mb.delete_dir()
    else:
        # Management command context
        localconfig = core_models.LocalConfig.objects.first()
        if not localconfig.parameters.get_value(
            "handle_mailboxes", raise_exception=False
        ):
            return
        mb.delete_dir()


@receiver(signals.post_delete, sender=models.Mailbox)
def remove_alias_for_mailbox(sender, instance, **kwargs):
    """Remove "self alias" for this mailbox."""
    models.Alias.objects.filter(address=instance.full_address).delete()


@receiver(core_signals.register_postfix_maps)
def register_postfix_maps(sender, **kwargs):
    """Register admin map files."""
    return [
        postfix_maps.DomainsMap,
        postfix_maps.DomainsAliasesMap,
        postfix_maps.AliasesMap,
        postfix_maps.MaintainMap,
        postfix_maps.SenderLoginMap,
    ]


@receiver(core_signals.account_auto_created)
def account_auto_created(sender, user, **kwargs):
    """New account has been auto-created, build the rest."""
    if not param_tools.get_global_parameter("auto_create_domain_and_mailbox"):
        return
    localpart, domname = split_mailbox(user.username)
    if user.role != "SimpleUsers" and domname is None:
        return
    sadmins = core_models.User.objects.filter(is_superuser=True)
    try:
        domain = models.Domain.objects.get(name=domname)
    except models.Domain.DoesNotExist:
        label = lib.check_if_domain_exists(
            domname, [(models.DomainAlias, _("domain alias"))]
        )
        if label is not None:
            return
        domain = models.Domain(name=domname, enabled=True, default_mailbox_quota=0)
        domain.save(creator=sadmins[0])
        for su in sadmins[1:]:
            permissions.grant_access_to_object(su, domain)
    qset = models.Mailbox.objects.filter(domain=domain, address=localpart)
    if not qset.exists():
        mb = models.Mailbox(
            address=localpart, domain=domain, user=user, use_domain_quota=True
        )
        mb.set_quota(override_rules=True)
        mb.save(creator=sadmins[0])
        user.email = mb.full_address
        user.save(update_fields=["email"])
        for su in sadmins[1:]:
            permissions.grant_access_to_object(su, mb)


@receiver(core_signals.account_exported)
def export_admin_domains(sender, user, **kwargs):
    """Export administered domains too."""
    result = [user.mailbox.quota] if hasattr(user, "mailbox") else [""]
    if user.role != "DomainAdmins":
        return result
    return result + [dom.name for dom in models.Domain.objects.get_for_admin(user)]


@receiver(core_signals.account_imported)
def import_account_mailbox(sender, user, account, row, **kwargs):
    """Handle extra fields when an account is imported.

    Expected fields:

    email address; quota; [domain; ...]

    :param User user: user importing the account
    :param User account: account being imported
    :param list rom: list of fields (strings)
    """
    account.email = row[0].strip().lower()
    if account.email:
        mailbox, domname = split_mailbox(account.email)
        domain = models.Domain.objects.filter(name=domname).first()
        if not domain:
            raise exceptions.BadRequest(
                _("Account import failed (%s): domain does not exist")
                % account.username
            )
        if not user.can_access(domain):
            raise exceptions.PermDeniedException
        core_signals.can_create_object.send(
            sender="import", context=user, klass=models.Mailbox
        )
        core_signals.can_create_object.send(
            sender="import", context=domain, object_type="mailboxes"
        )
        account.save()
        qset = models.Mailbox.objects.filter(address=mailbox, domain=domain)
        if qset.exists():
            raise exceptions.Conflict(
                _("Mailbox {} already exists").format(account.email)
            )
        if len(row) == 1:
            quota = None
        else:
            try:
                quota = int(row[1].strip())
            except ValueError:
                raise exceptions.BadRequest(
                    _("Account import failed (%s): wrong quota value")
                    % account.username
                ) from None
        use_domain_quota = True if not quota else False
        mb = models.Mailbox(
            address=mailbox,
            domain=domain,
            user=account,
            use_domain_quota=use_domain_quota,
        )
        mb.set_quota(quota, override_rules=user.has_perm("admin.change_domain"))
        mb.save(creator=user)
    if account.role == "DomainAdmins":
        for domname in row[2:]:
            try:
                dom = models.Domain.objects.get(name=domname.strip())
            except models.Domain.DoesNotExist:
                continue
            dom.add_admin(account)


@receiver(core_signals.account_role_changed)
def grant_access_to_all_objects(sender, account, role, **kwargs):
    """Grant all permissions if new role is SuperAdmin."""
    if role != "SuperAdmins":
        return
    perm_models = [
        core_models.User,
        models.Domain,
        models.DomainAlias,
        models.Mailbox,
        models.Alias,
    ]
    for model in perm_models:
        permissions.grant_access_to_objects(
            account, model.objects.all(), ContentType.objects.get_for_model(model)
        )


@receiver(admin_signals.import_object)
def get_import_func(sender, objtype, **kwargs):
    """Return function used to import objtype."""
    if objtype == "domain":
        return lib.import_domain
    elif objtype == "domainalias":
        return lib.import_domainalias
    elif objtype == "account":
        return lib.import_account
    elif objtype == "alias":
        return lib.import_alias
    elif objtype == "forward":
        return lib.import_forward
    elif objtype == "dlist":
        return lib.import_dlist
    return None


@receiver(signals.post_save, sender=core_models.User)
def disable_aliases_on_account_disabled(sender, instance, created, **kwargs):
    """Make sure aliases of a disabled account are also disabled."""
    if created or not hasattr(instance, "mailbox") or instance.is_active:
        return
    for alr in instance.mailbox.aliasrecipient_set.all().select_related("alias"):
        if alr.alias.recipients_count == 1:
            alr.alias.enabled = False
            alr.alias.save()
