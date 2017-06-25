from account.models import SignupCodeResult
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserConfig

class UserConfigInline(admin.StackedInline):
    model = UserConfig
    can_delete = False
    verbose_name_plural = 'config'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserConfigInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(SignupCodeResult)