from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from account.models import SignupCodeResult, SignupCode
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib import messages
from django.conf import settings
from datetime import datetime, timedelta
from django import forms
import account.forms
import account.views


from .models import InviteBatch
from uuid import uuid4
from io import StringIO, TextIOWrapper
from django.utils.translation import ugettext as _
import csv


class UploadFileForm(forms.Form):
    file = forms.FileField()


def invite_em(file):
    site = Site.objects.get_current()
    total = newly_added = 0
    reader = csv.DictReader(file, delimiter=";")
    results = StringIO()
    writer = csv.DictWriter(results, fieldnames=["first_name","last_name","email_address_1","invite_code"])

    writer.writeheader()

    for item in reader:
        total += 1
        email = item['email_address_1']
        first_name = item['first_name']
        last_name = item['last_name']

        try:
            code = SignupCode.objects.get(email=email)
        except SignupCode.DoesNotExist:
            code = SignupCode(email=email,
                              code=uuid4().hex[:20],
                              max_uses=1,
                              sent=datetime.utcnow(),
                              expiry=datetime.utcnow() + timedelta(days=14))
            newly_added += 1
            code.save()

            EmailMessage(
                    render_to_string("initadmin/email_invite_subject.txt"),
                    render_to_string("initadmin/email_invite_message.txt", context=dict(
                                     domain=site.domain,
                                     code=code,
                                     first_name=first_name)),
                    settings.DEFAULT_FROM_EMAIL,
                    [email]
                ).send()

        writer.writerow({
                "first_name": first_name,
                "last_name": last_name,
                "email_address_1": email,
                "invite_code": code.code
            })


    InviteBatch(payload=results.getvalue(), total_found=total, new_added=newly_added).save()

    return total, newly_added




class LoginEmailOrUsernameForm(account.forms.LoginEmailForm):

    email = forms.CharField(label=_("Email or Username"), max_length=50) 

class LoginView(account.views.LoginView):

    form_class = LoginEmailOrUsernameForm




# download imported files
@login_required
@user_passes_test(lambda u: u.is_staff)
def download_csv(request, id):
    batch = get_object_or_404(InviteBatch, pk=id)
    response = HttpResponse(batch.payload, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=invited_users.csv'
    return response

# (mass) invite users to the platform
@login_required
@user_passes_test(lambda u: u.is_staff)
def invite_users(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            total, send = invite_em(TextIOWrapper(request.FILES['file'].file, encoding=request.encoding))
            messages.success(request, "".join(["{}/{}".format(send, total), _("invitations were sent")]))
    else:
        form = UploadFileForm()
    return render(request, 'initadmin/invite_users.html', context=dict(form=form,
        invitebatches=InviteBatch.objects.order_by("-created_at")))

# active users (recently logged in first)
@login_required
@user_passes_test(lambda u: u.is_staff)
def active_users(request):
    users_q = get_user_model().objects.filter(is_active=True, avatar__primary=True).order_by("-last_login")
    return render(request, "initadmin/active_users.html", dict(users=users_q))

class UserEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name']

# edit own profile
@login_required
def profile_edit(request):
    user = get_object_or_404(get_user_model(), pk=request.user.id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.save():
            messages.success(request, _("Data updated."))
    else:
        form = UserEditForm(instance=user)
    return render(request, 'initadmin/profile_edit.html', context=dict(form=form))
