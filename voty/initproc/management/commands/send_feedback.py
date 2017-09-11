from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.template.loader import render_to_string

from voty.initproc.models import Initiative

"""
Send feedback to initiators of all initiatives that are already closed
"""

class Command(BaseCommand):
    help = "Send feedback to initiators for already closed initiatives"

    def handle(self, *args, **options):
        
        for i in Initiative.objects.exclude(was_closed_at__isnull=True):
            #send feedback message to all initiators
            EmailMessage(
                'Feedback zur Abstimmung',
                render_to_string('initadmin/voting_feedback.txt', context=dict(
                    target=i,
                    votecount = i.votes.count,
                    reasons = i.votes.values('reason').annotate(count=Count('reason'))
                )),
                settings.DEFAULT_FROM_EMAIL,
                [u.user.email for u in i.initiators]
            ).send()
