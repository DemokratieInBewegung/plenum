from account.models import SignupCodeResult
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.template.response import TemplateResponse
from random import randint
from .models import UserConfig

class UserConfigInline(admin.StackedInline):
    model = UserConfig
    can_delete = False
    verbose_name_plural = 'config'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserConfigInline, )

    actions = ['anonymize']

    def anonymize(self, request, queryset):
        if not request.POST.get('post'):
            # not confirmed yet; display the confirmation page
            return TemplateResponse(request,"initadmin/anonymize_users_confirmation.html", {
                'opts': self.model._meta,
                'users': queryset,
                'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            })

        # confirmed; anonymize the users
        count = queryset.count()
        if count:
            for user in queryset:
                user.first_name = ''
                user.last_name = ''
                user.email = ''
                user.is_staff = False  # for good measure
                user.is_active = False
                while True:
                    user.username = 'anon' + str(randint(1, 9999999999))
                    if not User.objects.filter(username=user.username).exists():
                        break
                user.save()

            self.message_user(request, "%d %s erfolgreich anonymisiert." % (count, model_ngettext(self.opts, count)), messages.SUCCESS)

        return None

    anonymize.short_description = 'Ausgewählte Benutzer*innen anonymisieren'

# gender-neutral verbose model name
User._meta.verbose_name = 'Benutzer*in'
User._meta.verbose_name_plural = 'Benutzer*innen'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(SignupCodeResult)

admin.site.register(Permission)