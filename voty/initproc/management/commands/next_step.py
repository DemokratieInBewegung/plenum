from django.core.management.base import BaseCommand, CommandError
from voty.initproc.models import Initiative
from voty.initproc.globals import STATES, NOTIFICATIONS
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.db.models import Count
from django.conf import settings
from django.contrib.auth import get_user_model
from math import ceil
from datetime import datetime, date

"""
Step models into the next step
"""

AUTOMATIC_STAGES = [ STATES.SEEKING_SUPPORT, STATES.DISCUSSION, STATES.VOTING ]

class Command(BaseCommand):
    help = "Move Initiative into next stage"

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int)

    def handle(self, *args, **options):

        id = options['id']
        if id:
            self.advance(Initiative.objects.get(id=id))
        else:
            for i in Initiative.objects.filter(state__in=AUTOMATIC_STAGES):
                if i.ready_for_next_stage and i.end_of_this_phase_date <= date.today():
                    self.advance(i)

    def advance(self, i):
                # phases incoming, prepare and moderation are entered through manual action

                if i.state == STATES.SEEKING_SUPPORT:
                    i.state = STATES.DISCUSSION
                    i.went_to_discussion_at = datetime.now()
                    i.save()
                    i.notify_followers(NOTIFICATIONS.INITIATIVE.WENT_TO_DISCUSSION)

                elif i.state == STATES.DISCUSSION:
                    i.state = STATES.FINAL_EDIT
                    i.save()
                    i.notify_initiators(NOTIFICATIONS.INITIATIVE.DISCUSSION_CLOSED)

                # voting phase is entered through manual action of moderators

                elif i.state == STATES.VOTING:
                    try:
                        i.state = i.get_vote_result()
                        i.eligible_voters = get_user_model().objects.filter(is_active=True).count()
                        i.was_closed_at = datetime.now()
                        i.save()
                        # if i.state == STATES.COMPLETED:
                        #     i.notify_followers(NOTIFICATIONS.INITIATIVE.COMPLETED) todo: define completed notification
                        # elif i.state == STATES.ACCEPTED:
                        #     i.notify_followers(NOTIFICATIONS.INITIATIVE.ACCEPTED) todo: define accepted notification
                        # elif i.state == STATES.REJECTED
                        #     i.notify_followers(NOTIFICATIONS.INITIATIVE.REJECTED) todo: define rejected notification

                        #send feedback message to all initiators
                        if not i.is_plenumoptions():
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

                    except Exception as e:
                        print(e)
                        print("Waiting for deadlock, not moving yet")
