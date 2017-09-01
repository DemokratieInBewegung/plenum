from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.text import slugify
from django.conf import settings
from reversion.models import Version

from pinax.notifications.models import send as notify
import reversion

from datetime import datetime, timedelta, date

from .globals import STATES, INITIATORS_COUNT, SPEED_PHASE_END
from django.db import models
import pytz


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

    einordnung = models.CharField(max_length=50, choices=[('Einzelinitiative','Einzelinitiative')])
    ebene = models.CharField(max_length=50, choices=[('Bund', 'Bund')])
    bereich = models.CharField(max_length=50, choices=[
                ('Mitbestimmung', 'Mitbestimmung'),
                ('Transparenz und Lobbyismus', 'Transparenz und Lobbyismus'),
                ('Demokratisches und solidarisches Europa', 'Demokratisches und solidarisches Europa'),
                ('Gerechtigkeit und Verantwortung füreinander', 'Gerechtigkeit und Verantwortung füreinander'),
                ('Vielfältige, weltoffene und inklusive Gesellschaft', 'Vielfältige, weltoffene und inklusive Gesellschaft'),
                ('Nachhaltigkeit', 'Nachhaltigkeit'),
                ('Zukunft aktiv gestalten', 'Zukunft aktiv gestalten'),
                ('(andere)', '(andere)')])

    went_public_at = models.DateField(blank=True, null=True)
    went_to_discussion_at = models.DateField(blank=True, null=True)
    went_to_voting_at = models.DateField(blank=True, null=True)
    was_closed_at = models.DateField(blank=True, null=True)

    variant_of = models.ForeignKey('self', blank=True, null=True, default=None, related_name="variants")

    supporters = models.ManyToManyField(User, through="Supporter")
    eligible_voters = models.IntegerField(blank=True, null=True)

    @cached_property
    def slug(self):
        return slugify(self.title)

    @cached_property
    def versions(self):
        return Version.objects.get_for_object(self)


    @cached_property
    def time_ramaining_in_phase(self):
        end_of_phase = self.end_of_this_phase

        if end_of_phase:
            return end_of_phase - datetime.today().date()

        return None

    @cached_property
    def ready_for_next_stage(self):

        if self.state in [Initiative.STATES.INCOMING, Initiative.STATES.MODERATION]:
            return self.supporting.filter(initiator=True, ack=True).count() == INITIATORS_COUNT

        if self.state in [Initiative.STATES.PREPARE, Initiative.STATES.FINAL_EDIT]:
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

        if self.state == Initiative.STATES.SEEKING_SUPPORT:
            return self.supporting.filter().count() >= self.quorum

        if self.state == Initiative.STATES.DISCUSSION:
            # there is nothing we have to accomplish
            return True

        if self.state == Initiative.STATES.VOTING:
            # there is nothing we have to accomplish
            return True

        return False


    @cached_property
    def end_of_this_phase(self):
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

                elif self.state == 'd':
                    return self.went_to_discussion_at + (3 * week)

                elif self.state == 'e':
                    return self.went_to_discussion_at + (5 * week)

                elif self.state == 'v':
                    return self.went_to_voting_at + (2 * week)

        return None

    @cached_property
    def quorum(self):
        return Quorum.current_quorum()

    @property
    def show_supporters(self):
        return self.state in [self.STATES.PREPARE, self.STATES.INCOMING, self.STATES.SEEKING_SUPPORT]

    @property
    def show_debate(self):
        return self.state in [self.STATES.DISCUSSION, self.STATES.FINAL_EDIT, self.STATES.MODERATION, self.STATES.VOTING]

    @cached_property
    def yays(self):
        return self.votes.filter(in_favor=True).count()

    @cached_property
    def nays(self):
        return self.votes.filter(in_favor=False).count()
      
    def is_accepted(self):
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
        return self.title;

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
    in_favor = models.BooleanField(default=True)
    reason = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = (("user", "initiative"),)

    @property
    def nay_survey_options(self):
        return settings.OPTIONAL_NOPE_REASONS



class Quorum(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    quorum = models.IntegerField(null=0)

    @classmethod
    def current_quorum(cls):
        return cls.objects.order_by("-created_at").values("quorum").first()["quorum"]


class Supporter(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    initiative = models.ForeignKey(Initiative, related_name="supporting")
    # whether this initiator has acknowledged they are
    ack = models.BooleanField(default=False)
    initiator = models.BooleanField(default=False)
    public = models.BooleanField(default=True)
    first = models.BooleanField(default=False)

    class Meta:
        unique_together = (("user", "initiative"),)



# Debating Models

class Like(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)

    target_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.IntegerField()
    target = GenericForeignKey('target_type', 'target_id')

    class Meta:
        unique_together = (("user", "target_type", "target_id"),)


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
    initiative = models.ForeignKey(Initiative, related_name="%(class)ss")

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