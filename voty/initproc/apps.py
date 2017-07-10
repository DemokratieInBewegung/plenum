from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .globals import NOTIFICATIONS

def create_notice_types(sender, **kwargs):

    from pinax.notifications.models import NoticeType
    print("Creating notices for Initproc")


    # Invitations
    NoticeType.create(NOTIFICATIONS.INVITE.SEND,
                      'Initativen Einladung',
                      'Du wurdest zu einer neuen Initiative eingeladen')

    NoticeType.create(NOTIFICATIONS.INVITE.ACCEPTED,
                      'Einladung angenommen',
                      'Die Einladung wurde angenommen')

    NoticeType.create(NOTIFICATIONS.INVITE.REJECTED,
                      'Einladung abgelehnt',
                      'Die Einladung wurde abgelehnt')


    # Initiative
    NoticeType.create(NOTIFICATIONS.INITIATIVE.EDITED,
                      'Initiative überarbeitet',
                      'Die Initiative wurde überarbeitet')

    NoticeType.create(NOTIFICATIONS.INITIATIVE.SUBMITTED,
                      'Initiative eingereicht',
                      'Die Initiative wurde eingereicht')

    NoticeType.create(NOTIFICATIONS.INITIATIVE.PUBLISHED,
                      'Initiative veröffentlicht',
                      'Die Initiative wurde veröffentlicht')

    NoticeType.create(NOTIFICATIONS.INITIATIVE.WENT_TO_DISCUSSION,
                      'Initiative in Diskussion',
                      'Die Initiative ist in die Diskussionphase eingetreten')


    NoticeType.create(NOTIFICATIONS.INITIATIVE.WENT_TO_VOTE,
                      'Initiative in Abstimmung',
                      'Die Initiative ist in die Abstimmung gegangen')

    # DISCUSSION

    NoticeType.create(NOTIFICATIONS.INITIATIVE.NEW_ARGUMENT,
                      'Neues Argument in Diskussion zur Initiative',
                      'Es wurde ein neues Argument in der Diskussion zur Initiative gepostet')


class InitprocConfig(AppConfig):
    name = 'voty.initproc'
    verbose_name ="Inititive Process"

    def ready(self):
        post_migrate.connect(create_notice_types, sender=self)