from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .globals import NOTIFICATIONS
from django.utils.translation import ugettext as _

def create_notice_types(sender, **kwargs):

    from pinax.notifications.models import NoticeType
    print("Creating notices for Initproc")

    # Invitations
    NoticeType.create(NOTIFICATIONS.INVITE.SEND,
                      _("Invitation to Initiative"),
                      _("You have been invitied to a new Initiative"))
    NoticeType.create(NOTIFICATIONS.INVITE.ACCEPTED,
                      _("Invitation accepted"),
                      _("The Invitation was accepted"))
    NoticeType.create(NOTIFICATIONS.INVITE.REJECTED,
                      _("Invitation declined"),
                      _("The Invitation was declined"))

    # Initiative
    NoticeType.create(NOTIFICATIONS.INITIATIVE.EDITED,
                      _("Initiative modified"),
                      _("The Initiative was modified"))
    NoticeType.create(NOTIFICATIONS.INITIATIVE.SUBMITTED,
                      _("Initiative submitted"),
                      _("The Initiative was submitted"))
    NoticeType.create(NOTIFICATIONS.INITIATIVE.PUBLISHED,
                      _("Initiative published"),
                      _("The Initiative was published"))
    NoticeType.create(NOTIFICATIONS.INITIATIVE.WENT_TO_DISCUSSION,
                      _("Initiative in discussion"),
                      _("The Initiative has been moved to the discussion phase"))
    NoticeType.create(NOTIFICATIONS.INITIATIVE.DISCUSSION_CLOSED,
                      _("Discussion for Initiative ended"),
                      _("The Initiative can now be finally modified"))
    NoticeType.create(NOTIFICATIONS.INITIATIVE.WENT_TO_VOTE,
                      _("Initiative in Vote"),
                      _("The Initiative has been put to Vote"))

    # Discussion
    NoticeType.create(NOTIFICATIONS.INITIATIVE.NEW_ARGUMENT,
                      _("New Argument in Discussion for Initiative"),
                      _("A new Argument was postet in the Discussion for the Initiative"))

class InitprocConfig(AppConfig):
    name = "voty.initproc"
    verbose_name = "Initiative Process"

    def ready(self):
        post_migrate.connect(create_notice_types, sender=self)
