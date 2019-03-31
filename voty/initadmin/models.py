from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
import pytz

class InviteBatch(models.Model):
	created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
	total_found = models.IntegerField(default=0)
	new_added = models.IntegerField(default=0)
	payload = models.TextField()



class UserConfig(models.Model):
    user = models.OneToOneField(User, related_name="config", on_delete=models.CASCADE)
    is_diverse_mod = models.BooleanField(default=False)
    is_female_mod = models.BooleanField(default=False)
    last_activity = models.DateTimeField(default=None, null=True, blank=True)

    def act(self):
        self.last_activity = timezone.now()
        self.save()

