from django.core.management.base import BaseCommand, CommandError
from voty.initproc.models import Quorum, IssueSupportersQuorum, IssueVotersQuorum
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from math import ceil

"""
- Bis 99 Abstimmungsberechtigten 10 Personen
- ab 100 bis 299 Abstimmungsberechtigten 15 Personen
- ab 300 bis 599 Abstimmungsberechtigten 20 Personen
- ab 600 bis 999 Abstimmungsberechtigten 30 Personen
- ab 1000 bis 1999 Abstimmungsberechtigten 35 Personen
- ab 2000 bis 4999 Abstimmungsberechtigten 50 Personen
- ab 5000 Abstimmungsberechtigten 1% der Abstimmungsberechtigten
"""

class Command(BaseCommand):
    help = "Calculate the next quorum and set it"

    def handle(self, *args, **options):
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
        total = get_user_model().objects.filter(is_active=True, config__last_activity__gt=threshold).count()
        totalpartymembers = get_user_model().objects.filter(is_active=True, config__is_party_member=True, config__last_activity__gt=threshold).count()
        
        print("Total active users: {}".format(total))
        print("Total active party members: {}".format(totalpartymembers))
        
        #Quorum for Issue Support
        quorum = ceil(total / 20.0)
        if quorum < 5:
            quorum = 5
        IssueSupportersQuorum(value=quorum).save()
        print("Issue Support Quorum set to {}".format(quorum))
        
        #Quorum for Issue Voting
        quorum = ceil(totalpartymembers / 10.0)
        if quorum < 5:
            quorum = 5
        #commented out because it is now set manually, 10% of all party members, not only of those who have a login or are active in Plenum
        #IssueVotersQuorum(value=quorum).save()
        #print("Issue Voting Quorum set to {}".format(quorum))
        
        quorum = ceil(total / 100.0)

        if total < 100:
            quorum = 10
        elif total < 300:
            quorum = 15
        elif total < 600:
            quorum = 20
        elif total < 1000:
            quorum = 30
        elif total < 2000:
            quorum = 35
        elif total < 5000:
            quorum = 50

        Quorum(quorum=quorum).save()

        print("Initiatives Quorum set to {}".format(quorum))