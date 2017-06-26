from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.apps import apps
from django.db.models import Q
from dal import autocomplete
from django import forms
from datetime import datetime
from django_ajax.decorators import ajax
from pinax.notifications.models import send as notify

from .globals import NOTIFICATIONS, STATES, INITIATORS_COUNT
from .guard import can_access_initiative
from .models import (Initiative, Pro, Contra, Proposal, Comment, Vote, Moderation, Quorum, Supporter, Like)
from .forms import (simple_form_verifier, InitiativeForm, NewArgumentForm, NewCommentForm,
                    NewProposalForm, NewModerationForm, InviteUsersForm)
# Create your views here.

DEFAULT_FILTERS = [
    STATES.PREPARE,
    STATES.INCOMING,
    STATES.SEEKING_SUPPORT,
    STATES.DISCUSSION,
    STATES.VOTING]



def param_as_bool(param):
    try:
        return bool(int(param))
    except ValueError:
        return param.lower() in ['true', 'y', 'yes', '✔', '✔️', 'j', 'ja' 'yay', 'yop', 'yope']

#
# ____    ____  __   ___________    __    ____   _______.
# \   \  /   / |  | |   ____\   \  /  \  /   /  /       |
#  \   \/   /  |  | |  |__   \   \/    \/   /  |   (----`
#   \      /   |  | |   __|   \            /    \   \    
#    \    /    |  | |  |____   \    /\    / .----)   |   
#     \__/     |__| |_______|   \__/  \__/  |_______/    
#
#                                                       


def ueber(request):
    return render(request, 'static/ueber.html',context=dict(
            quorums=Quorum.objects.order_by("-created_at")))


def index(request):
    filters = [f for f in request.GET.getlist("f")] or DEFAULT_FILTERS
    inits = request.guard.make_intiatives_query(filters)
    count_inbox = request.guard.make_intiatives_query(['i']).count()

    return render(request, 'initproc/index.html',context=dict(initiatives=inits,
                    inbox_count=count_inbox, filters=filters))



class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return get_user_model().objects.none()

        qs = get_user_model().objects.all()

        if self.q:
            qs = qs.filter(Q(first_name__startswith=self.q) | Q(last_name__startswith=self.q) | Q(username__startswith=self.q))

        return qs


@login_required
def new(request):
    form = InitiativeForm()
    if request.method == 'POST':
        form = InitiativeForm(request.POST)
        if form.is_valid():
            ini = form.save(commit=False)
            ini.state = STATES.PREPARE
            ini.save()

            Supporter(initiative=ini, user=request.user, initiator=True, ack=True, public=True).save()
            return redirect('/initiative/{}-{}'.format(ini.id, ini.slug))
        else:
            messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

    return render(request, 'initproc/new.html', context=dict(form=form))


@can_access_initiative()
def item(request, init, slug=None):

    ctx = dict(initiative=init,
               proposals=[x for x in init.proposals.prefetch_related('likes').all()],
               arguments=[x for x in init.pros.prefetch_related('likes').all()] +\
                         [x for x in init.contras.prefetch_related('likes').all()])

    ctx['arguments'].sort(key=lambda x: (x.likes.count(), x.created_at), reverse=True)
    ctx['proposals'].sort(key=lambda x: (x.likes.count(), x.created_at), reverse=True)


    if request.user.is_authenticated:
        user_id = request.user.id
        ctx.update({'has_supported': init.supporting.filter(user=user_id).count(),
                    'has_voted': init.votes.filter(user=user_id).count()})
        if ctx['has_voted']:
            ctx['vote'] = init.votes.filter(user=user_id).first().vote

        for arg in ctx['arguments'] + ctx['proposals']:
            arg.has_liked = arg.likes.filter(user=user_id).count() > 0
            if arg.user.id == user_id:
                arg.has_commented = True
            else:
                for cmt in arg.comments.all():
                    if cmt.user.id == user_id:
                        arg.has_commented = True
                        break

    return render(request, 'initproc/item.html', context=ctx)


@ajax
@can_access_initiative()
def show_resp(request, initiative, target_type, target_id, slug=None):

    model_cls = apps.get_model('initproc', target_type)
    arg = get_object_or_404(model_cls, pk=target_id)

    assert arg.initiative == initiative, "How can this be?"

    ctx = dict(argument=arg,
               has_commented=False,
               can_like=False,
               has_liked=False,
               comments=arg.comments.order_by('-created_at').all())

    if request.user.is_authenticated:
        ctx['has_liked'] = arg.likes.filter(user=request.user).count() > 0
        if arg.user == request.user:
            ctx['has_commented'] = True
            # users can self-like at the moment...

    return {'fragments': {
        '#{arg.type}-{arg.id}'.format(arg=arg): render_to_string('fragments/argument/full.html',
                                                                 context=ctx, request=request)
        }}

@ajax
@login_required
@can_access_initiative(None, 'can_moderate')
def show_moderation(request, initiative, target_id, slug=None):
    arg = get_object_or_404(Moderation, pk=target_id)

    assert arg.initiative == initiative, "How can this be?"

    ctx = dict(m=arg,
               has_commented=False,
               can_like=False,
               has_liked=False,
               comments=arg.comments.order_by('-created_at').all())

    if request.user:
        ctx['has_liked'] = arg.likes.filter(user=request.user).count() > 0
        if arg.user == request.user:
            ctx['has_commented'] = True
            # users can self-like at the moment...

    return {'fragments': {
        '#{arg.type}-{arg.id}'.format(arg=arg): render_to_string('fragments/moderation/full.html',
                                                                 context=ctx, request=request)
        }}


#
#      ___       ______ .___________. __    ______   .__   __.      _______.
#     /   \     /      ||           ||  |  /  __  \  |  \ |  |     /       |
#    /  ^  \   |  ,----'`---|  |----`|  | |  |  |  | |   \|  |    |   (----`
#   /  /_\  \  |  |         |  |     |  | |  |  |  | |  . `  |     \   \    
#  /  _____  \ |  `----.    |  |     |  | |  `--'  | |  |\   | .----)   |   
# /__/     \__\ \______|    |__|     |__|  \______/  |__| \__| |_______/    
#
#
#                                                                        

@login_required
@can_access_initiative([STATES.PREPARE, STATES.FINAL_EDIT], 'can_edit')
def edit(request, initiative):
    form = InitiativeForm(request.POST or None, instance=initiative)
    if request.method == 'POST':
        if form.is_valid():
            initiative.save()
            messages.success(request, "Initiative gespeichert.")
            initiative.notify_followers(NOTIFICATIONS.INITIATIVE.EDITED, subject=request.user)
            return redirect('/initiative/{}'.format(initiative.id))
        else:
            messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

    return render(request, 'initproc/new.html', context=dict(form=form, initiative=initiative))


@login_required
@can_access_initiative(STATES.PREPARE, 'can_edit')
def submit_to_committee(request, initiative):
    if initiative.ready_for_next_stage:
        initiative.state = STATES.INCOMING
        initiative.save()

        messages.success(request, "Deine Initiative wurde angenommen und wird geprüft.")
        initiative.notify_followers(NOTIFICATIONS.INITIATIVE.SUBMITTED, subject=request.user)
        return redirect('/initiative/{}'.format(initiative.id))
    else:
        messages.warning(request, "Die Bedingungen für die Einreichung sind nicht erfüllt.")

    return redirect('/initiative/{}'.format(initiative.id))



@ajax
@login_required
@can_access_initiative(STATES.PREPARE, 'can_edit') 
@simple_form_verifier(InviteUsersForm, submit_title="Einladen")
def invite(request, form, initiative, invite_type):
    for user in form.cleaned_data['user']:
        if invite_type == 'initiators' and \
            initiative.supporting.filter(initiator=True).count() >= INITIATORS_COUNT:
            break

        try:
            supporting = initiative.supporting.get(user_id=user.id)
        except Supporter.DoesNotExist:
            supporting = Supporter(user=user)
            supporting.initiative = initiative

        if invite_type == 'initiators':
            supporting.initiator = True
        elif invite_type == 'supporters':
            supporting.first = True
        supporting.ack = False
        supporting.save()

        notify([user], NOTIFICATIONS.INVITE.SEND, {"target": initiative}, sender=request.user)

    messages.success(request, "Initiatoren eingeladen." if invite_type == 'initiators' else 'Unterstützer eingeladen.' )
    return redirect("/initiative/{}-{}".format(initiative.id, initiative.slug))




@require_POST
@login_required
@can_access_initiative(STATES.SEEKING_SUPPORT, 'can_support') # must be seeking for supporters
def support(request, initiative):
    Supporter(initiative=initiative, user_id=request.user.id,
              public=not not request.POST.get("public", False)).save()

    return redirect('/initiative/{}'.format(initiative.id))


@require_POST
@login_required
@can_access_initiative([STATES.PREPARE, STATES.INCOMING])
def ack_support(request, initiative):
    sup = get_object_or_404(Supporter, initiative=initiative, user_id=request.user.id)
    sup.ack = True
    sup.save()

    messages.success(request, "Danke für die Bestätigung")
    initiative.notify_followers(NOTIFICATIONS.INVITE.ACCEPTED, subject=request.user)

    return redirect('/initiative/{}'.format(initiative.id))


@require_POST
@login_required
@can_access_initiative([STATES.SEEKING_SUPPORT, STATES.INCOMING, STATES.PREPARE])
def rm_support(request, initiative):
    sup = get_object_or_404(Supporter, initiative=initiative, user_id=request.user.id)
    sup.delete()

    messages.success(request, "Deine Unterstützung wurde zurückgezogen")
    initiative.notify_followers(NOTIFICATIONS.INVITE.REJECTED, subject=request.user)

    if initiative.state == 's':
        return redirect('/initiative/{}'.format(initiative.id))
    return redirect('/')



@ajax
@login_required
@can_access_initiative(STATES.DISCUSSION) # must be in discussion
@simple_form_verifier(NewArgumentForm)
def new_argument(request, form, initiative):
    data = form.cleaned_data
    argCls = Pro if data['type'] == "👍" else Contra

    arg = argCls(initiative=initiative,
                 user_id=request.user.id,
                 title=data['title'],
                 text=data['text'])

    arg.save()

    return {
        'inner-fragments': {'#new-argument': "<strong>Danke für dein Argument</strong>"},
        'append-fragments': {'#argument-list': render_to_string("fragments/argument/small.html",
                                                  context=dict(argument=arg),
                                                  request=request)}
    }



@ajax
@login_required
@can_access_initiative(STATES.DISCUSSION) # must be in discussion
@simple_form_verifier(NewProposalForm)
def new_proposal(request, form, initiative):
    data = form.cleaned_data
    proposal = Proposal(initiative=initiative,
                        user_id=request.user.id,
                        text=data['text'])

    proposal.save()

    return {
        'inner-fragments': {'#new-proposal': "<strong>Danke für deinen Vorschlag</strong>"},
        'append-fragments': {'#proposal-list': render_to_string("fragments/argument/small.html",
                                                  context=dict(argument=proposal),
                                                  request=request)}
    }


@ajax
@login_required
@can_access_initiative('i', 'can_moderate') # must be in discussion
@simple_form_verifier(NewModerationForm)
def moderate(request, form, initiative):
    model = form.save(commit=False)
    model.initiative = initiative
    model.user = request.user
    model.save()

    if request.guard.can_publish(initiative):
        initiative.supporting.filter(ack=False).delete()
        initiative.went_public_at = datetime.now()
        initiative.state = STATES.SEEKING_SUPPORT
        initiative.save()

        messages.success(request, "Initiative veröffentlicht")
        initiative.notify_followers(NOTIFICATIONS.INITIATIVE.PUBLISHED)
        initiative.notify_moderators(NOTIFICATIONS.INITIATIVE.PUBLISHED, subject=request.user)

        return redirect('/initiative/{}'.format(initiative.id))

    
    return {
        'inner-fragments': {'#moderation-new': "<strong>Eintrag aufgenommen</strong>",
                            '#moderation-list'.format(initiative.id):
                                render_to_string("fragments/moderation/list_small.html",
                                                  context=dict(initiative=initiative),
                                                  request=request)}
    }



@ajax
@login_required
@simple_form_verifier(NewCommentForm)
def comment(request, form, target_type, target_id):
    data = form.cleaned_data
    model_cls = apps.get_model('initproc', target_type)
    model = get_object_or_404(model_cls, pk=target_id)

    cmt = Comment(target=model, user=request.user, **data)
    cmt.save()

    return {
        'inner-fragments': {'#{}-new-comment'.format(model.unique_id):
                "<strong>Danke für deine Kommentar</strong>"},
        'append-fragments': {'#{}-comment-list'.format(model.unique_id):
            render_to_string("fragments/comment/item.html",
                             context=dict(comment=cmt),
                             request=request)}
    }


@ajax
@login_required
def like(request, target_type, target_id):
    model_cls = apps.get_model('initproc', target_type)
    model = get_object_or_404(model_cls, pk=target_id)

    ctx = {"target": model, "show_text": False, "show_count": True, "has_liked": True}
    for key in ['show_text', 'show_count']:
        if key in request.GET:
            ctx[key] = param_as_bool(request.GET[key])

    Like(target=model, user=request.user).save()
    return {'fragments': {
        '#{}-like'.format(model.unique_id): render_to_string("fragments/like.html",
                                                             context=ctx,
                                                             request=request)
    }}


@ajax
@login_required
def unlike(request, target_type, target_id):
    model_cls = apps.get_model('initproc', target_type)
    model = get_object_or_404(model_cls, pk=target_id)

    model.likes.filter(user_id=request.user.id).delete()

    ctx = {"target": model, "show_text": False, "show_count": True, "has_liked": False}
    for key in ['show_text', 'show_count']:
        if key in request.GET:
            ctx[key] = param_as_bool(request.GET[key])

    return {'fragments': {
        '#{}-like'.format(model.unique_id): render_to_string("fragments/like.html",
                                                             context=ctx,
                                                             request=request)
    }}



@require_POST
@login_required
@can_access_initiative(STATES.VOTING) # must be in voting
def vote(request, init, vote):
    in_favor = vote != 'nay'
    my_vote = Vote.objects.get(initiative=init, user_id=request.user)
    if my_vote:
        if my_vote.in_favor != in_favor:
            my_vote.in_favor = in_favor
            my_vote.save()
    else:
        Vote(initiative=initiative, user_id=request.user.id, in_favor=in_favor).save()

    return redirect('/initiative/{}'.format(initiative.id))