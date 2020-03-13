from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.text import slugify
from django.conf import settings
from reversion.models import Version

from pinax.notifications.models import send as notify
import reversion

from datetime import datetime, timedelta, date

from .globals import NOTIFICATIONS, STATES, VOTED, INITIATORS_COUNT, SPEED_PHASE_END, ABSTENTION_START, VOTY_TYPES, CONTRIBUTION_QUORUM, BOARD_GROUP
from django.db import models
import pytz

from voty.initproc.globals import SUBJECT_CATEGORIES, ADMINISTRATIVE_LEVELS


class IssueSupportersQuorum(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    value = models.IntegerField(null=0)

    @classmethod
    def current_value(cls):
        return cls.objects.order_by("-created_at").values("value").first()["value"]
        
        
class IssueVotersQuorum(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    value = models.IntegerField(null=0)

    @classmethod
    def current_value(cls):
        return cls.objects.order_by("-created_at").values("value").first()["value"]
    
@reversion.register()
class Issue(models.Model):
    title = models.CharField(max_length=80, unique=True)
    motivation = models.TextField(max_length=1000, blank=True)
    level = models.CharField(max_length=50, choices=[
            ('Bund', 'Bund'),
            ('Baden-Württemberg', 'Baden-Württemberg'),
            ('Bayern', 'Bayern'),
            ('Berlin', 'Berlin'),
            ('Brandenburg', 'Brandenburg'),
            ('Bremen', 'Bremen'),
            ('Hamburg', 'Hamburg'),
            ('Hessen', 'Hessen'),
            ('Mecklenburg-Vorpommern', 'Mecklenburg-Vorpommern'),
            ('Niedersachsen', 'Niedersachsen'),
            ('Nordrhein-Westfalen', 'Nordrhein-Westfalen'),
            ('Rheinland-Pfalz', 'Rheinland-Pfalz'),
            ('Saarland', 'Saarland'),
            ('Sachsen', 'Sachsen'),
            ('Sachsen-Anhalt', 'Sachsen-Anhalt'),
            ('Schleswig-Holstein', 'Schleswig-Holstein'),
            ('Thüringen', 'Thüringen')
        ], default='Bund')
    
    createdate = models.DateTimeField(auto_now_add=True)
    changedate = models.DateTimeField(auto_now=True)
    
    # fallback 
    STATES = STATES 

    status = models.CharField(max_length=1, choices=[
            (STATES.PREPARE, "preparation"),
            (STATES.INCOMING, "review"),
            (STATES.SEEKING_SUPPORT, "seeking support"),
            (STATES.DISCUSSION, "in discussion"),
            (STATES.MODERATION, "in discussion, final review"),
            (STATES.VOTING, "is being voted on"),
            (STATES.VETO, "overcome veto"),
            (STATES.COMPLETED, "was completed")
        ],
        default=STATES.PREPARE)
    # MODERATION = reviewing issue's solutions
    
    went_to_review_at = models.DateField(blank=True, null=True)
    went_to_seeking_support_at = models.DateField(blank=True, null=True)
    went_to_discussion_at = models.DateField(blank=True, null=True)
    went_to_final_review_at = models.DateField(blank=True, null=True)
    went_to_voting_at = models.DateField(blank=True, null=True)
    went_to_veto_phase_at = models.DateField(blank=True, null=True)
    was_closed_at = models.DateField(blank=True, null=True)    

    @property
    def is_open(self):
        return self.was_closed_at is not None

    @cached_property
    def slug(self):
        return slugify(self.title)
        
    def __str__(self):
        return self.title

    @cached_property
    def versions(self):
        return Version.objects.get_for_object(self)

    @cached_property
    def supporters_quorum(self):
        if self.level == 'Bund':
            return IssueSupportersQuorum.current_value()
        """ FIXME: field config.state is missing
        now = timezone.now()
        year = now.year
        month = now.month
        # round to turn of month
        if now.day > 15:
            month += 1
        month -= 6
        if month < 1:
            year -= 1
            month += 12
        threshold = timezone.datetime(year=year, month=month, day=1, tzinfo=now.tzinfo)
        totalusers = get_user_model().objects.filter(is_active=True, config__state=self.level, config__last_activity__gt=threshold).count()
        return = ceil(totalusers / 20.0)
        """
        
    @cached_property
    def voters_quorum(self):
        if self.level == 'Bund':
            return IssueVotersQuorum.current_value()
        """ FIXME: field config.state is missing
        now = timezone.now()
        year = now.year
        month = now.month
        # round to turn of month
        if now.day > 15:
            month += 1
        month -= 6
        if month < 1:
            year -= 1
            month += 12
        threshold = timezone.datetime(year=year, month=month, day=1, tzinfo=now.tzinfo)
        totalpartymembers = get_user_model().objects.filter(is_active=True, config__is_party_member=True, config__state=self.level, config__last_activity__gt=threshold).count()
        return = ceil(totalpartymembers / 10.0)
        """

    @cached_property
    def end_of_current_phase(self):
        week = timedelta(days=7)
        halfyear = timedelta(days=183)

        if self.went_to_review_at:
            if self.was_closed_at:
                return self.was_closed_at + halfyear # locked for 6 months
            if self.status == self.STATES.VETO:
                return self.went_to_veto_phase_at + (2 * week)
            if self.status == self.STATES.VOTING:
                return self.went_to_voting_at + (2 * week)
            if self.status == self.STATES.MODERATION:
                return self.went_to_final_review_at + (1 * week)
            if self.status == self.STATES.DISCUSSION:
                return self.went_to_discussion_at + (2 * week)
            if self.status == self.STATES.SEEKING_SUPPORT:
                return self.went_to_seeking_support_at + (2 * week)
        return None

    @cached_property
    def initiators(self):
        return self.supporters.filter(initiator=True).order_by("created_at")
        
    @cached_property
    def supporters_count(self):
        return self.supporters.count()

    @cached_property
    def relative_support(self):
        return self.supporters_count / self.supporters_quorum * 100
        
    @property
    def show_supporters(self):
        return self.status in [self.STATES.PREPARE, self.STATES.INCOMING, self.STATES.SEEKING_SUPPORT]

    @property
    def in_discussion(self):
        return self.went_to_discussion_at is not None and self.went_to_voting_at is None

    @property
    def in_voting_phase(self):
        return self.status == self.STATES.VOTING
        
    @cached_property
    def has_veto(self):
        for s in self.solutions.all():
            if s.refusing.exists():
                return True
        return False
        
    @cached_property
    def get_veto(self):
        for s in self.solutions.all():
            if s.refusing.exists():
                return s.refusing.first().user.get_full_name() + ': ' + s.refusing.first().reason
        return None
        
    @cached_property
    def failed_review(self):
        if self.went_to_review_at is not None and self.went_to_seeking_support_at is None and self.was_closed_at is not None:
            return True
        return False
        
    @cached_property
    def missed_supporters_quorum(self):
        if self.went_to_seeking_support_at is not None and self.went_to_discussion_at is None and self.was_closed_at is not None:
            return True
        return False
        
    @cached_property
    def missed_voters_quorum(self):
        if self.went_to_voting_at is not None:
            if self.went_to_veto_phase_at is None:
                return True
        return False
        
    @cached_property
    def ready_for_review(self):
        if self.status in [STATES.INCOMING, STATES.PREPARE]:
            #has no empty text fields and 3 initiators
            return (self.title) and self.supporters.filter(initiator=True, ack=True).count() == INITIATORS_COUNT
        return False
        
        
    def notify_initiators(self, *args, **kwargs):
        query = [s.user for s in self.initiators]
        return self.notify(query, *args, **kwargs)
        
    

    def notify_moderators(self, *args, **kwargs):
        return self.notify([m.user for m in self.issuemoderations.all()], *args, **kwargs)
    
    def notify_final_review(self):
        moderation_permission = Permission.objects.filter(content_type__app_label='initproc', codename='add_review')
        self.notify(get_user_model().objects.filter(groups__permissions=moderation_permission, is_active=True).all(),
                              NOTIFICATIONS.ISSUE.FINAL_REVIEW, subject=request.user)

    def notify_followers(self, *args, **kwargs):
        query = [s.user for s in self.supporters.filter(ack=True).all()] if self.status == STATES.PREPARE else [s.user for s in self.supporters.all()]
        return self.notify(query, *args, **kwargs)

    def notify_board(self, *args, **kwargs):
        query = get_user_model().objects.filter(groups__name=BOARD_GROUP, is_active=True)
        return self.notify(query, *args, **kwargs)
        
    def notify(self, recipients, notice_type, extra_context=None, subject=None, **kwargs):
        context = extra_context or dict()
        if subject:
            kwargs['sender'] = subject
            context['target'] = self
        else:
            kwargs['sender'] = self

        notify(recipients, notice_type, context, **kwargs)
        
        

    @property
    def current_moderations(self):
        return self.issuemoderations.filter(stale=False)

    @property
    def stale_moderations(self):
        return self.issuemoderations.filter(stale=True)
        
    @property
    def has_unreviewed_solutions(self):
        return self.solutions.filter(status='d').count() > 0


@reversion.register()
class Solution(models.Model):
    issue = models.ForeignKey(Issue, related_name="solutions")
    user = models.ForeignKey(User)
    title = models.CharField(max_length=80)
    description = models.TextField(max_length=1000, blank=True)
    budget = models.IntegerField(null=0)
    createdate = models.DateTimeField(auto_now_add=True)
    changedate = models.DateTimeField(auto_now=True)
    
    # fallback 
    STATES = STATES 

    status = models.CharField(max_length=1, choices=[
            (STATES.DISCUSSION, "in discussion"),
            (STATES.ACCEPTED, "review passed"),
            (STATES.REJECTED, "rejected by review")
        ],
        default=STATES.DISCUSSION)
    
    passed_review_at = models.DateTimeField(blank=True, null=True)

    @property
    def is_visible(self):
        return self.status != self.STATES.REJECTED
        
    @property
    def has_arguments(self):
        return (self.proslist.count() > 0 or self.contraslist.count() > 0)
        
    @property
    def is_commentable(self):
        return self.status != self.STATES.REJECTED and self.issue.went_to_discussion_at is not None and self.issue.went_to_voting_at is None
        
        
    @property
    def current_moderations(self):
        return self.moderationslist.filter(stale=False)

    @property
    def stale_moderations(self):
        return self.moderationslist.filter(stale=True)

    @cached_property
    def slug(self):
        return slugify(self.title)
        
    def __str__(self):
        return self.title

    @cached_property
    def versions(self):
        return Version.objects.get_for_object(self)
    
    def notify_creator(self, *args, **kwargs):
        query = [self.user]
        return self.notify(query, *args, **kwargs)
        
    def notify_moderators(self, *args, **kwargs):
        return self.notify([m.user for m in self.moderationslist.all()], *args, **kwargs)
        
    def notify(self, recipients, notice_type, extra_context=None, subject=None, **kwargs):
        context = extra_context or dict()
        if subject:
            kwargs['sender'] = subject
            context['target'] = self
        else:
            kwargs['sender'] = self

        notify(recipients, notice_type, context, **kwargs)
    
    class Meta:
        unique_together = ("issue", "title")
    
    
class Veto(models.Model):
    createdate = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    solution = models.ForeignKey(Solution, related_name="refusing")
    reason = models.TextField(max_length=1000)

    class Meta:
        unique_together = ("user", "solution")



class Topic(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    closes_at = models.DateTimeField(blank=True, null=True)
    topic = models.TextField(blank=True)
    subtitle = models.CharField(max_length=1024, blank=True)
    motivation = models.TextField(blank=True)

    def now(self):
        return datetime.now(self.closes_at.tzinfo)

    @cached_property
    def slug(self):
        return slugify(self.topic)

    @property
    def open_ended(self):
        return self.closes_at is None

    @property
    def submission_ends(self):
        return self.closes_at - timedelta(weeks=1)

    @property
    def is_archived(self):
        return self.closes_at and self.now() > self.closes_at

    @property
    def soliciting_resistance(self):
        return not (self.is_archived or self.open_ended or self.now() < self.submission_ends)

    @property
    def accepting_submissions(self):
        return not (self.is_archived or self.soliciting_resistance)

    @property
    def end_of_this_phase(self):
        return self.submission_ends if self.accepting_submissions else self.closes_at

@reversion.register()
class Initiative(models.Model):

    # fallback 
    STATES = STATES 

    title = models.CharField(max_length=80)
    subtitle = models.CharField(max_length=1024, blank=True)
    state = models.CharField(max_length=1, choices=[
            (STATES.PREPARE, "preparation"),
            (STATES.INCOMING, "new arrivals"),
            (STATES.SEEKING_SUPPORT, "seeking support"),
            (STATES.DISCUSSION, "in discussion"),
            (STATES.FINAL_EDIT, "final edits"),
            (STATES.MODERATION, "with moderation team"),
            (STATES.HIDDEN, "hidden"),
            (STATES.VOTING, "is being voted on"),
            (STATES.COMPLETED, "was completed"),
            (STATES.ACCEPTED, "was accepted"),
            (STATES.REJECTED, "was rejected")
        ])

    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)

    summary = models.TextField(blank=True)
    problem = models.TextField(blank=True)
    forderung = models.TextField(blank=True)
    kosten = models.TextField(blank=True)
    fin_vorschlag = models.TextField(blank=True)
    arbeitsweise = models.TextField(blank=True)
    init_argument = models.TextField(blank=True)

    einordnung = models.CharField(max_length=50, choices=[
        (VOTY_TYPES.Einzelinitiative,'Einzelinitiative'),
        (VOTY_TYPES.PolicyChange,'AO-Änderung'),
        (VOTY_TYPES.BallotVote,'Urabstimmung'),
        (VOTY_TYPES.PlenumVote,'Plenumsentscheidung'),
        (VOTY_TYPES.PlenumOptions,'Plenumsabwägung'),
        (VOTY_TYPES.Contribution,'Beitrag'),
    ])
    ebene = models.CharField(max_length=50, choices=[(item,item) for item in ADMINISTRATIVE_LEVELS])
    bereich = models.CharField(max_length=60, choices=[(item,item) for item in SUBJECT_CATEGORIES])

    went_public_at = models.DateField(blank=True, null=True)
    went_to_discussion_at = models.DateField(blank=True, null=True)
    went_to_voting_at = models.DateField(blank=True, null=True)
    was_closed_at = models.DateField(blank=True, null=True)

    variant_of = models.ForeignKey('self', blank=True, null=True, default=None, related_name="variants")

    supporters = models.ManyToManyField(User, through="Supporter")
    eligible_voters = models.IntegerField(blank=True, null=True)

    topic = models.ForeignKey(Topic, blank=True, null=True, default=None)

    @cached_property
    def slug(self):
        return slugify(self.title)

    @cached_property
    def versions(self):
        return Version.objects.get_for_object(self)


    @cached_property
    def sort_index(self):
        return self.type_priority + self.time_index

    @cached_property
    def type_priority(self):
        return timedelta(days = 0 if self.is_initiative() else -1000000)

    @cached_property
    def time_index(self):
        timezone = self.created_at.tzinfo
        if self.was_closed_at: #recently closed first
            return datetime.today().date() - self.was_closed_at

        elif self.end_of_this_phase: #closest to deadline first
            return self.end_of_this_phase_date - datetime.today().date()

        else: #newest first
            return datetime.now(timezone) - self.created_at

    @cached_property
    def ready_for_next_stage(self):
        if self.is_initiative():
            return self.initiative_ready_for_next_stage

        if self.is_policychange():
            return self.policy_change_ready_for_next_stage

        if self.is_plenumvote():
            return self.plenumvote_ready_for_next_stage

        if self.is_plenumoptions(): # TODO: check that options are non-empty
            return self.plenumvote_ready_for_next_stage

        if self.is_contribution():
            return self.contribution_ready_for_next_stage

    @cached_property
    def initiative_ready_for_next_stage(self):
        if self.state in [STATES.INCOMING, STATES.MODERATION]:
            return self.supporting.filter(initiator=True, ack=True).count() == INITIATORS_COUNT

        if self.state in [STATES.PREPARE, STATES.FINAL_EDIT]:
            #three initiators and no empty text fields
            return (self.supporting.filter(initiator=True, ack=True).count() == INITIATORS_COUNT and
                    self.title and
                    self.subtitle and
                    self.arbeitsweise and
                    self.bereich and
                    self.ebene and
                    self.einordnung and
                    self.fin_vorschlag and
                    self.forderung and
                    self.init_argument and
                    self.kosten and
                    self.problem and
                    self.summary)

        if self.state == STATES.SEEKING_SUPPORT:
            return self.supporting.filter().count() >= self.quorum

        if self.state == STATES.DISCUSSION:
            # there is nothing we have to accomplish
            return True

        if self.state == STATES.VOTING:
            # there is nothing we have to accomplish
            return True

        return False

    @cached_property
    def policy_change_ready_for_next_stage(self):
        if self.state in [STATES.PREPARE, STATES.FINAL_EDIT]:
            #no empty text fields
            return (self.title and
                    self.subtitle and
                    self.summary)

        if self.state == STATES.DISCUSSION:
            # there is nothing we have to accomplish
            return True

        if self.state == STATES.VOTING:
            # there is nothing we have to accomplish
            return True

        return False

    @cached_property
    def plenumvote_ready_for_next_stage(self):
        if self.state in [STATES.PREPARE, STATES.FINAL_EDIT]:
            #no empty text fields
            return (self.title and
                    self.subtitle and
                    self.summary)

        if self.state == STATES.VOTING:
            # there is nothing we have to accomplish
            return True

        return False

    @cached_property
    def contribution_ready_for_next_stage(self):
        if self.state in [STATES.PREPARE]:
            #no empty text fields
            return (self.title and
                    self.subtitle and
                    self.summary)

        return True

    @cached_property
    def end_of_this_phase_date(self):
        return self.end_of_this_phase.date() if hasattr(self.end_of_this_phase,'date') else self.end_of_this_phase

    @cached_property
    def end_of_this_phase(self):
        if self.is_initiative():
            return self.initiative_end_of_this_phase

        if self.is_policychange():
            return self.policy_change_end_of_this_phase

        if self.is_plenumvote():
            return self.plenumvote_end_of_this_phase

        if self.is_plenumoptions():
            return self.plenumoptions_end_of_this_phase

        if self.is_contribution():
            return self.contribution_end_of_this_phase

    @cached_property
    def initiative_end_of_this_phase(self):
        week = timedelta(days=7)
        halfyear = timedelta(days=183)

        if self.was_closed_at:
            return self.was_closed_at + halfyear # Half year later.

        if self.went_public_at:
            if self.went_public_at < SPEED_PHASE_END:
                if self.state == Initiative.STATES.SEEKING_SUPPORT:
                    if self.variant_of:
                        if self.variant_of.went_to_discussion_at:
                            return self.variant_of.went_to_discussion_at + (2 * week)
                    if self.ready_for_next_stage:
                        return self.went_public_at + week
                    return self.went_public_at + halfyear

                elif self.state == Initiative.STATES.DISCUSSION:
                    base = self.went_to_discussion_at
                    if self.variant_of:
                        if self.variant_of.went_to_discussion_at:
                            base = self.variant_of.went_to_discussion_at
                    return base + (2 * week)

                elif self.state == 'e':
                    return self.went_to_discussion_at + (3 * week)

                elif self.state == 'v':
                    return self.went_to_voting_at + week

            else:
                if self.state == Initiative.STATES.SEEKING_SUPPORT:
                    if self.variant_of:
                        if self.variant_of.went_to_discussion_at:
                            return self.variant_of.went_to_discussion_at +( 2 * week)
                    if self.ready_for_next_stage:
                        return self.went_public_at + (2 * week)
                    return self.went_public_at + halfyear

                elif self.state == 'd':
                    return self.went_to_discussion_at + (3 * week)

                elif self.state == 'e':
                    return self.went_to_discussion_at + (5 * week)

                elif self.state == 'v':
                    return self.went_to_voting_at + (3 * week)

        return None

    @cached_property
    def policy_change_end_of_this_phase(self):
        week = timedelta(days=7)
        halfyear = timedelta(days=183)

        if self.was_closed_at:
            return self.was_closed_at + halfyear # Half year later.

        if self.went_to_discussion_at:
            if self.state == STATES.DISCUSSION:
                return self.went_to_discussion_at + (3 * week)

            elif self.state == STATES.FINAL_EDIT:
                return self.went_to_discussion_at + (5 * week)

            elif self.state == STATES.VOTING:
                return self.went_to_voting_at + (2 * week)

        return None

    @cached_property
    def plenumvote_end_of_this_phase(self):
        duration = timedelta(days=4,hours=18)
        halfyear = timedelta(days=183)

        if self.was_closed_at:
            return self.was_closed_at + halfyear # Half year later.

        if self.state == STATES.VOTING:
            at = self.went_to_voting_at
            return datetime(year=at.year,month=at.month,day=at.day) + duration

        return None

    @cached_property
    def plenumoptions_end_of_this_phase(self):
        duration = timedelta(days=4,hours=12)
        halfyear = timedelta(days=183)

        if self.was_closed_at:
            return self.was_closed_at + halfyear # Half year later.

        if self.state == STATES.VOTING:
            at = self.went_to_voting_at
            return datetime(year=at.year,month=at.month,day=at.day) + duration

        return None

    @cached_property
    def contribution_end_of_this_phase(self):
        if self.topic.open_ended:
            return self.went_public_at + timedelta(weeks=3)
        if self.state == 'v':
            return self.topic.closes_at
        return self.topic.submission_ends

    @cached_property
    def has_phase_end(self):
        return not (self.state in [self.STATES.INCOMING, self.STATES.COMPLETED, self.STATES.ACCEPTED, self.STATES.REJECTED, self.STATES.PREPARE, self.STATES.MODERATION] or (self.is_contribution() and self.topic.open_ended and self.state != self.STATES.DISCUSSION))

    @cached_property
    def german_gender(self):
        return 'm' if self.is_contribution() else 'f'

    @cached_property
    def quorum(self):
        return CONTRIBUTION_QUORUM if self.is_contribution() else Quorum.current_quorum()

    @property
    def show_supporters(self):
        return self.state in [self.STATES.PREPARE, self.STATES.INCOMING, self.STATES.SEEKING_SUPPORT]

    @property
    def show_responses(self):
        return self.state in [self.STATES.DISCUSSION, self.STATES.FINAL_EDIT, self.STATES.MODERATION, self.STATES.VOTING, self.STATES.COMPLETED, self.STATES.ACCEPTED, self.STATES.REJECTED]

    @property
    def seeks_resistance(self):
        return self.is_contribution() and self.topic.open_ended and self.state == self.STATES.DISCUSSION

    @cached_property
    def yays(self):
        return self.votes.filter(value=VOTED.YES).count()

    @cached_property
    def nays(self):
        return self.votes.filter(value=VOTED.NO).count()

    @cached_property
    def abstains(self):
        return self.votes.filter(value=VOTED.ABSTAIN).count()

    def get_vote_result(self):
        if self.is_plenumoptions() or self.is_contribution():
            return STATES.COMPLETED
        if self.is_accepted():
            return STATES.ACCEPTED
        return STATES.REJECTED

    def is_accepted(self):
        if self.is_initiative():
            return self.initiative_is_accepted()

        if self.is_policychange():
            return self.policy_change_is_accepted()

        if self.is_plenumvote():
            return self.plenumvote_is_accepted()

    def is_initiative(self):
        return self.einordnung is None or self.einordnung == VOTY_TYPES.Einzelinitiative

    def is_policychange(self):
        return self.einordnung == VOTY_TYPES.PolicyChange

    def is_plenumvote(self):
        return self.einordnung == VOTY_TYPES.PlenumVote

    def is_plenumoptions(self):
        return self.einordnung == VOTY_TYPES.PlenumOptions

    def is_contribution(self):
        return self.einordnung == VOTY_TYPES.Contribution

    def is_passive_solution(self):
        return self.is_contribution() and self.title == "Passivlösung"

    def subject(self):
        if self.is_initiative():
            return 'Initiative'
        if self.is_policychange():
            return 'AO-Änderung'
        if self.is_plenumvote():
            return 'Vorlage'
        if self.is_plenumoptions():
            return 'Vorlage'

    def initiative_is_accepted(self):
        if self.yays <= self.nays: #always reject if too few yays
            return False

        if(self.all_variants):
            most_votes = 0
            for ini in self.all_variants: #find the variant that
                if ini.yays > ini.nays:       # was accepted
                   if ini.yays > most_votes:   # and has the most yay votes
                       most_votes = ini.yays
            # then check if current initiative has more than the highest variant
            if self.yays > most_votes:
                return True
            elif self.yays == most_votes:
                print("We have a tie. Problem! {}".format(self.title))
                # self.notify_moderators("???")
                raise Exception("Wait until one of them wins")
            else:
                return False

        # no variants:
        return self.yays > self.nays

    def policy_change_is_accepted(self):
        if self.yays > (self.nays * 2): #two third majority
            return True

        return False

    def plenumvote_is_accepted(self):
        if self.yays > (self.nays): #simple majority
            return True

        return False

    @cached_property
    def all_variants(self):
        if self.variants.count():
            return self.variants.all()

        if self.variant_of:
            variants = [self.variant_of]
            if self.variant_of.variants.count() > 1:
                for ini in self.variant_of.variants.all():
                    if ini.id == self.id: continue
                    variants.append(ini)

            return variants 

        return []

    # FIXME: cache this
    @cached_property
    def absolute_supporters(self):
        return self.supporting.count()

    @cached_property
    def relative_support(self):
        return self.absolute_supporters / self.quorum * 100

    @cached_property
    def first_supporters(self):
        return self.supporting.filter(first=True).order_by("-created_at")

    @cached_property
    def public_supporters(self):
        return self.supporting.filter(public=True, first=False, initiator=False).order_by("-created_at")

    @cached_property
    def initiators(self):
        return self.supporting.filter(initiator=True).order_by("created_at")

    @cached_property
    def custom_cls(self):
        return 'item-{} state-{} area-{}'.format(slugify(self.title),
                    slugify(self.state), slugify(self.bereich))

    @cached_property
    def allows_abstention(self):
        if self.went_to_voting_at:
            return self.went_to_voting_at > ABSTENTION_START
        else:
            return True

    @property
    def current_moderations(self):
        return self.moderations.filter(stale=False)

    @property
    def stale_moderations(self):
        return self.moderations.filter(stale=True)

    @cached_property
    def eligible_voter_count(self):
        if self.eligible_voters: #is set when initiative is closed
            return self.eligible_voters
        else: # while open, number of voters == number of users
            return get_user_model().objects.filter(is_active=True).count()

    def __str__(self):
        return self.title

    def notify_moderators(self, *args, **kwargs):
        return self.notify([m.user for m in self.moderations.all()], *args, **kwargs)

    def notify_followers(self, *args, **kwargs):
        query = [s.user for s in self.supporting.filter(ack=True).all()] if self.state == 'p' else self.supporters.all()

        return self.notify(query, *args, **kwargs)

    def notify_initiators(self, *args, **kwargs):
        query = [s.user for s in self.initiators]
        return self.notify(query, *args, **kwargs)

    def notify(self, recipients, notice_type, extra_context=None, subject=None, **kwargs):
        context = extra_context or dict()
        if subject:
            kwargs['sender'] = subject
            context['target'] = self
        else:
            kwargs['sender'] = self

        notify(recipients, notice_type, context, **kwargs)

class Vote(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    initiative = models.ForeignKey(Initiative, related_name="votes")
    CHOICES = [
        (VOTED.YES, "Ja"),
        (VOTED.NO, "Nein"),
        (VOTED.ABSTAIN, "Enthaltung")]
    value = models.IntegerField(choices=CHOICES)
    reason = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = (("user", "initiative"),)

    @property
    def nay_survey_options(self):
        return settings.OPTIONAL_NOPE_REASONS

    @cached_property
    def in_favor(self):
        return self.value == VOTED.YES

    @cached_property
    def against(self):
        return self.value == VOTED.NO

    @cached_property
    def abstained(self):
        return self.value == VOTED.ABSTAIN

class Option(models.Model):
    initiative = models.ForeignKey(Initiative, related_name="options")
    text = models.TextField()
    index = models.IntegerField()

    class Meta:
        ordering = ['index']

class Weight(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    value = models.IntegerField()

    class Meta:
        abstract = True

# "Preference" was a bit of misnomer. Both Preference and Resistance represent resistance values,
# for plenum options and for agora contributions, respectively

# for plenum options
class Preference(Weight):
    option = models.ForeignKey(Option, related_name="preferences")

    class Meta:
        unique_together = (("user", "option"),)
        ordering = ['option__index']

# for agora contributions (=Topic's Initiatives) / Issue Solutions
class Resistance(Weight):
    contribution = models.ForeignKey(Initiative, related_name="resistances", null=True)
    solution = models.ForeignKey(Solution, related_name="rating", null=True)
    reason = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = (("user", "contribution"),("user", "solution"))


class Quorum(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    quorum = models.IntegerField(null=0)

    @classmethod
    def current_quorum(cls):
        return cls.objects.order_by("-created_at").values("quorum").first()["quorum"]


class Supporter(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    initiative = models.ForeignKey(Initiative, related_name="supporting", null=True)
    issue = models.ForeignKey(Issue, related_name="supporters", null=True)
    # whether this initiator has acknowledged they are
    ack = models.BooleanField(default=False)
    initiator = models.BooleanField(default=False)
    public = models.BooleanField(default=True)
    first = models.BooleanField(default=False)

    class Meta:
        unique_together = (("user", "initiative"),("user", "issue"))



# Debating Models

class Like(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)

    target_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.IntegerField()
    target = GenericForeignKey('target_type', 'target_id')

    class Meta:
        unique_together = ("user", "target_type", "target_id")


### Abstracts

class Likeable(models.Model):
    class Meta:
        abstract = True

    likes_count = models.IntegerField(default=0) # FIXME: should be updated per DB-trigger
    likes = GenericRelation(Like,
                            content_type_field='target_type',
                            object_id_field='target_id')


class Comment(Likeable):
    type = "comment"
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)

    target_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.IntegerField()
    target = GenericForeignKey('target_type', 'target_id')

    text = models.CharField(max_length=500)

    @property
    def unique_id(self):
        return "{}-{}".format(self.type, self.id)


class Commentable(models.Model):
    class Meta:
        abstract = True

    comments_count = models.IntegerField(default=0) # FIXME: should be updated per DB-trigger
    comments = GenericRelation(Comment,
                               content_type_field='target_type',
                               object_id_field='target_id')


class Response(Likeable, Commentable):
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, related_name="%(class)ss")
    initiative = models.ForeignKey(Initiative, related_name="%(class)ss", null=True)
    solution = models.ForeignKey(Solution, related_name="%(class)sslist", null=True)

    class Meta:
        abstract = True

    @property
    def unique_id(self):
        return "{}-{}".format(self.type, self.id)


class Argument(Response):
    title = models.CharField(max_length=140)
    text = models.CharField(max_length=500)

    class Meta:
        abstract = True

### End of Abstract

class Question(Response):
    type = "question"
    icon = False
    title = models.CharField(max_length=140)
    text = models.CharField(max_length=1024)

class Proposal(Response):
    type = "proposal"
    icon = False
    title = models.CharField(max_length=140)
    text = models.CharField(max_length=1024)

class Pro(Argument):
    type = "pro"
    css_class = "success"
    icon = "thumb_up"

    def __str__(self):
        return "Pro: {}".format(self.title)

class Contra(Argument):
    type = "contra"
    css_class = "danger"
    icon = "thumb_down"

    def __str__(self):
        return "Kontra: {}".format(self.title)

class Moderation(Response):
    type = "moderation"
    stale = models.BooleanField(default=False)
    vote = models.CharField(max_length=1, choices=[
            ('y', 'okay'),
            ('a', 'abstain'),
            ('r', 'request'),
            ('n', 'no!')
        ])
    text = models.CharField(max_length=500, blank=True)
    issue = models.ForeignKey(Issue, related_name="issuemoderations", null=True)

    class Meta:
        unique_together = (("user", "initiative"),("user", "issue"),("user", "solution"))
