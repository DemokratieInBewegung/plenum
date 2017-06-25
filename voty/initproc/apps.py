from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .globals import NOTIFICATIONS

def create_notice_types(sender, **kwargs):

    from pinax.notifications.models import NoticeType
    print("Creating notices for Initproc") 

    NoticeType.create(NOTIFICATIONS.INVITED,
                      'Initativen Einladung',
                      'Du wurdest zu einer neuen Initiative eingeladen')

class InitprocConfig(AppConfig):
    name = 'voty.initproc'
    verbose_name ="Inititive Process"

    def ready(self):
        post_migrate.connect(create_notice_types, sender=self)