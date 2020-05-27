from django.core.management.base import BaseCommand, CommandError
from voty.initproc.models import Initiative, Issue
from voty.initproc.globals import STATES, NOTIFICATIONS
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.db.models import Count
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, date
from .set_quorum import Command as QuorumCommand

"""
Step models into the next step
"""

AUTOMATIC_STAGES = [ STATES.SEEKING_SUPPORT, STATES.DISCUSSION, STATES.VOTING ]

class Command(BaseCommand):
    help = "Move Initiative into next stage"

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int)

    def handle(self, *args, **options):
        if date.today().day == 1:
            QuorumCommand().handle()

        id = options['id']
        if id:
            self.advance(Initiative.objects.get(id=id))
        else:
            for i in Initiative.objects.filter(state__in=AUTOMATIC_STAGES):
                if i.ready_for_next_stage and i.end_of_this_phase_date <= date.today():
                    self.advance(i)
                    
            for i in Issue.objects.filter(status__in=[STATES.SEEKING_SUPPORT,STATES.DISCUSSION,STATES.MODERATION,STATES.VOTING,STATES.VETO]):
                if i.end_of_current_phase <= date.today():
                    self.advance_issue(i)

    def advance(self, i):
                # phases incoming, prepare and moderation are entered through manual action

                if i.state == STATES.SEEKING_SUPPORT:
                    i.state = STATES.DISCUSSION
                    i.went_to_discussion_at = datetime.now()
                    i.save()
                    if not i.is_contribution():
                        # TODO: fix notifications for contributions
                        i.notify_followers(NOTIFICATIONS.INITIATIVE.WENT_TO_DISCUSSION)

                elif i.state == STATES.DISCUSSION:
                    i.state = (STATES.COMPLETED if i.topic.open_ended else STATES.VOTING) if i.is_contribution() else STATES.FINAL_EDIT
                    i.save()
                    if not i.is_contribution():
                        # TODO: fix notifications for contributions
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
                        if not (i.is_plenumoptions() or i.is_contribution()):
                            # TODO: fix notifications for contributions
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
            
    def advance_issue(self, i):
        # phases prepare and incoming are entered through manual action
    
        if i.status == STATES.SEEKING_SUPPORT: # did not get enough suppoters, so close
            i.status = STATES.COMPLETED
            i.was_closed_at = datetime.now()
            i.save()
            i.notify_followers(NOTIFICATIONS.ISSUE.CLOSED)
    
        elif i.status == STATES.DISCUSSION:
            i.status = STATES.MODERATION
            i.went_to_final_review_at = datetime.now()
            i.save()
            i.notify_final_review()
    
        elif i.status == STATES.MODERATION:
            if i.solutions.filter(status='d').count() == 0 and i.solutions.filter(status='a').count() > 0:
                i.status = STATES.VOTING
                i.went_to_voting_at = datetime.now()
                i.save()
                i.notify_initiators(NOTIFICATIONS.ISSUE.WENT_TO_VOTE)
    
        elif i.status == STATES.VOTING:
            if i.solutions.exclude(status='r').first().rating.count() >= i.voters_quorum:
                i.status = STATES.VETO
                i.went_to_veto_phase_at = datetime.now()
                i.notify_board(NOTIFICATIONS.ISSUE.VOTED)
            else:
                i.status = STATES.COMPLETED
                i.was_closed_at = datetime.now()
            i.save()
    
        elif i.status == STATES.VETO:
            i.status = STATES.COMPLETED
            i.was_closed_at = datetime.now()
            i.save()
            i.notify_initiators(NOTIFICATIONS.ISSUE.COMPLETED)