from django.contrib.auth.models import User
from django.db import models


class Initiative(models.Model):
    STATES = (('n', 'new'),
    		  ('d', 'discussion'),
    		  ('v', 'voting'),
    		  ('a', 'accepted'),
    		  ('r', 'rejected'))

    title = models.CharField(max_length=80)
    state = models.CharField(max_length=1, choices=STATES)
    quorum = models.IntegerField(default=30)

    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)

    summary = models.TextField()
    forderung = models.TextField()
    kosten = models.TextField()
    fin_vorschlag = models.TextField()
    arbeitsweise = models.TextField()
    init_argument = models.TextField()

    einordnung = models.CharField(max_length=50)
    ebene = models.CharField(max_length=50)
    bereich = models.CharField(max_length=50)

    initiators = models.ManyToManyField(User)

    went_to_discussion_at = models.DateTimeField(blank=True, null=True)
    went_to_voting_at = models.DateTimeField(blank=True, null=True)
    was_closed_at = models.DateTimeField(blank=True, null=True)

    @property
    def yays(self):
        print(self.votes)
        return self.votes.filter(Vote.in_favor==True).count()

    @property
    def nays(self):
        return self.votes.filter(Vote.in_favor==False).count()

    @property
    def relative_support(self):
        return self.supporters.count() / self.quorum * 100

    @property
    def public_supporters(self):
        return self.supporters.filter(public=True)



class Supporter(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    initiative = models.ForeignKey(Initiative, related_name="supporters")
    public = models.BooleanField(default=True)

    class Meta:
        unique_together = (("user", "initiative"),)


class DemandingVote(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    initiative = models.ForeignKey(Initiative, related_name="demands")
    public = models.BooleanField(default=True)

    class Meta:
        unique_together = (("user", "initiative"),)


class Argument(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    initiative = models.ForeignKey(Initiative, related_name="arguments")
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



from django.contrib import admin
admin.site.register(Initiative)
admin.site.register(Supporter)
admin.site.register(DemandingVote)
admin.site.register(Argument)
admin.site.register(Comment)
admin.site.register(Vote)