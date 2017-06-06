from django.contrib.auth.models import User
from datetime import datetime, timedelta, date
from django.db import models
import pytz

SPEED_PHASE_END = date(2017, 8, 21) # Everything published before this has speed phase


class Initiative(models.Model):
    class STATES:
        INCOMING = 'i'
        SEEKING_SUPPORT = 's'
        DISCUSSION = 'd'
        FINAL_EDIT = 'e'
        MODERATION = 'm'
        HIDDEN = 'h'
        VOTING = 'v'
        ACCEPTED = 'a'
        REJECTED = 'r'

    title = models.CharField(max_length=80)
    state = models.CharField(max_length=1, choices=[
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
    quorum = models.IntegerField(default=30)

    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)

    summary = models.TextField()
    forderung = models.TextField()
    kosten = models.TextField()
    fin_vorschlag = models.TextField()
    arbeitsweise = models.TextField()
    init_argument = models.TextField()

    einordnung = models.CharField(max_length=50, choices=[('Einzellinitiatve','Einzellinitiative')])
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

    initiators = models.ManyToManyField(User)

    went_public_at = models.DateField(blank=True, null=True)
    went_to_discussion_at = models.DateField(blank=True, null=True)
    went_to_voting_at = models.DateField(blank=True, null=True)
    was_closed_at = models.DateField(blank=True, null=True)


    @property
    def time_ramaining_in_phase(self):
        end_of_phase = self.end_of_this_phase

        if end_of_phase:
            return end_of_phase - datetime.today().date()

        return None

    @property
    def end_of_this_phase(self):
        today = datetime.today().date()
        week = timedelta(days=7)
        halfyear = timedelta(days=183)

        if self.was_closed_at:
            return self.was_closed_at + halfyear # Half year later.

        if self.went_public_at:
            if self.went_public_at < SPEED_PHASE_END:
                if self.state == 's':
                    if self.went_public_at + week < today:
                        return self.went_public_at + halfyear
                    return self.went_public_at + week

                elif self.state == 'd':
                    return self.went_to_discussion_at + (2 * week)

                elif self.state == 'e':
                    return self.went_to_discussion_at + (3 * week)

                elif self.state == 'v':
                    return self.went_to_voting_at + week

            else:
                if self.state == 's':
                    if today - self.went_public_at > (2 * week):
                        return self.went_public_at + halfyear
                    return self.went_public_at + (2 * week)

                elif self.state == 'd':
                    return self.went_to_discussion_at + (3 * week)

                elif self.state == 'e':
                    return self.went_to_discussion_at + (5 * week)

                elif self.state == 'v':
                    return self.went_to_voting_at + (2 * week)

        return None


    @property
    def yays(self):
        print(self.votes)
        return self.votes.filter(Vote.in_favor==True).count()

    @property
    def nays(self):
        return self.votes.filter(Vote.in_favor==False).count()

    # FIXME: cache this
    @property
    def absolute_supporters(self):
        return self.supporters.count() + self.initiators.count()

    @property
    def relative_support(self):
        return self.absolute_supporters / self.quorum * 100

    @property
    def first_supporters(self):
        return self.supporters.filter(first=True)

    @property
    def public_supporters(self):
        return self.supporters.filter(public=True)



class Supporter(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    initiative = models.ForeignKey(Initiative, related_name="supporters")
    public = models.BooleanField(default=True)
    first = models.BooleanField(default=False)

    class Meta:
        unique_together = (("user", "initiative"),)


class Argument(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    initiative = models.ForeignKey(Initiative, related_name="arguments")
    title = models.CharField(max_length=80)
    text = models.TextField()
    in_favor = models.BooleanField(default=True)


class Comment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    argument = models.ForeignKey(Argument, related_name="comments")
    text = models.TextField()


class Like(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    argument = models.ForeignKey(Argument, related_name="likes")

    class Meta:
        unique_together = (("user", "argument"),)

class Vote(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    initiative = models.ForeignKey(Initiative, related_name="votes")
    in_favor = models.BooleanField(default=True)

    class Meta:
        unique_together = (("user", "initiative"),)