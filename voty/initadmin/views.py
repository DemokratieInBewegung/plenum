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
import csv

from voty.initproc.models import Initiative, Vote

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
                    'Dein Einladungscode zur DiB Abstimmungsplattform',
                    render_to_string('initadmin/email_invite.txt', context=dict(
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


@login_required
@user_passes_test(lambda u: u.is_staff)
def download_csv(request, id):
    batch = get_object_or_404(InviteBatch, pk=id)
    response = HttpResponse(batch.payload, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=mass_invited.csv'
    return response

@login_required
@user_passes_test(lambda u: u.is_staff)
def mass_invite(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            total, send = invite_em(TextIOWrapper(request.FILES['file'].file, encoding=request.encoding))
            messages.success(request, "Coolio. Aus {} sind {} neue Einladungen versand worden".format(total, send))
    else:
        form = UploadFileForm()

    return render(request, 'initadmin/mass_invite.html', context=dict(form=form,
        invitebatches=InviteBatch.objects.order_by("-created_at")))

@login_required
@user_passes_test(lambda u: u.is_staff)
def export_results(request):
    results = StringIO()
    fieldnames = ["Titel", "Abschlussdatum","Abstimmungsberechtigte"]
    for (value,name) in Vote.CHOICES:
        fieldnames.append(name)
    print (fieldnames)
    writer = csv.DictWriter(results, fieldnames=fieldnames)
    writer.writeheader()
    for initiative in sorted (Initiative.objects.filter(was_closed_at__isnull=False), key=lambda x: x.was_closed_at):
        row = {
                "Titel": initiative.title,
                "Abschlussdatum": initiative.was_closed_at.strftime("%d. %m. %Y"),
                "Abstimmungsberechtigte": initiative.eligible_voters
            }
        for (value,name) in Vote.CHOICES:
            row [name] = initiative.votes.filter(value=value).count()

        writer.writerow(row)

    response=HttpResponse(results.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=results.csv'
    return response

class UserEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name']


def avatar_wall(request):
    # showing recently logged in first should give us a neat randomization over time
    users_q = get_user_model().objects.filter(is_active=True, avatar__primary=True).order_by("-last_login")
    return render(request, "initadmin/avatar_wall.html", dict(users=users_q))


@login_required
def profile_edit(request):
    user = get_object_or_404(get_user_model(), pk=request.user.id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.save():
            messages.success(request, "Daten aktualisiert.")
    else:
        form = UserEditForm(instance=user)

    return render(request, 'initadmin/profile_edit.html', context=dict(form=form))


class LoginEmailOrUsernameForm(account.forms.LoginEmailForm):

    email = forms.CharField(label="Email oder Benutzername", max_length=50) 

class LoginView(account.views.LoginView):

    form_class = LoginEmailOrUsernameForm