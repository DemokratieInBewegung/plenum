from account.models import SignupCode
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from voty.initadmin.models import UserConfig

import csv

class Command(BaseCommand):
    help = "Identify party members based on their signup codes"

    def add_arguments(self, parser):
        parser.add_argument('--members') # the name of a CSV file containing signup codes of party members

    def handle(self, *args, **options):
        print(options)
        members = options['members']
        reader = csv.DictReader(open(members, "r"), delimiter=";")

        member_count = 0

        for item in reader:
            code = item ['Einladungsschlüssel zum Abstimmungstool']
            codes = SignupCode.objects.filter(code=code)
            count = codes.count()
            if count != 1:
                print("code %s occurs %d times" % (code, count))
            else:
                results = codes.get().signupcoderesult_set
                count = results.count()
                if count != 1:
                    print("code %s corresponds to %d results" % (code, count))
                else:
                    config = results.get().user.config
                    config.is_party_member = True
                    config.save()

                    member_count += 1

        print("member flag was set for %d members" % member_count)
