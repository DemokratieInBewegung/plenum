from django.core.management.base import BaseCommand
from voty.initproc.models import Vote, Supporter, Like, Comment, Proposal, Pro, Contra, Moderation
import datetime
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Output statistics on most recent activities of users"

    dates = {}

    def addDate(self, user, date):
        self.dates [user] = max (self.dates [user], date) if user in self.dates else date

    def handleModel (self, model):
        for o in model.objects.all ():
            self.addDate (o.user, max (o.changed_at, o.created_at) if hasattr(o, 'changed_at') else o.created_at)

    def handle(self, *args, **options):
        self.handleModel (Vote)
        self.handleModel (Supporter)
        self.handleModel (Like)
        self.handleModel (Comment)
        self.handleModel (Proposal)
        self.handleModel (Pro)
        self.handleModel (Contra)
        self.handleModel (Moderation)

        for user in self.dates.keys():
            self.dates [user] = self.dates [user].date()

        today = datetime.date.today()

        corpse = today
        for date in self.dates.values ():
            corpse = min(corpse, date)

        counts = [0] * ((today - corpse).days + 2)
        for date in self.dates.values():
            counts [(today - date).days + 1] += 1

        # now counts [d] is the number of users whose most recent activity was d days ago

        print("uncumulated")
        for i in range (0, len(counts)):
            print ("{} {}".format(i, counts [i]))

        for i in range (1, len (counts)):
            counts [i] += counts [i - 1]
        
        # now counts [d] is the number of users whose most recent activity was at most d days ago

        print()
        print("cumulated")
        for i in range (0, len(counts)):
            print ("{} {}".format(i, counts [i]))
            
        print()
        print("total: %s " % User.objects.filter(is_active=True).count())
