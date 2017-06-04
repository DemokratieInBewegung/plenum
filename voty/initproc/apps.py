from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_notice_types(sender, **kwargs):

    from pinax.notifications.models import NoticeType
    print("Creating notices for Initproc") 
    
    NoticeType.create("my_init_published", "Eigene Initiative veröffentlicht", "Deine Initiative wurde veröffentlich. Starte jetzt deine Suche nach Unterstützern!")

    NoticeType.create("new_init_published", "Neue Intiative veröffentlicht", "Eine neue Initiative wurde veröffentlicht")

class InitprocConfig(AppConfig):
    name = 'voty.initproc'
    verbose_name ="Inititive Process"

    def ready(self):
        post_migrate.connect(create_notice_types, sender=self)