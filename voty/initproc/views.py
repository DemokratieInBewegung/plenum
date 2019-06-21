from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.decorators import available_attrs
from django.utils.safestring import mark_safe
from django.contrib.postgres.search import SearchVector
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
from django.apps import apps
from django.db.models import Q
from django.db import connection
from dal import autocomplete
from django import forms

from datetime import datetime, timedelta
from django.utils import timezone

from rest_framework.renderers import JSONRenderer
from django_ajax.shortcuts import render_to_json
from django_ajax.decorators import ajax
from pinax.notifications.models import send as notify
from reversion_compare.helpers import html_diff
from reversion.models import Version
import reversion

from functools import wraps
import json

from .globals import NOTIFICATIONS, STATES, VOTED, INITIATORS_COUNT, COMPARING_FIELDS, VOTY_TYPES, BOARD_GROUP
from .guard import can_access_initiative
from .models import (Initiative, Pro, Contra, Proposal, Question, Comment, Vote, Option, Preference, Resistance, Moderation, Quorum, Supporter, Like, Topic)
from .forms import (simple_form_verifier, InitiativeForm, NewArgumentForm, NewCommentForm, NewQuestionForm,
                    NewProposalForm, NewModerationForm, InviteUsersForm, PolicyChangeForm, PlenumVoteForm, PlenumOptionsForm, ContributionForm)
from .serializers import SimpleInitiativeSerializer
from django.contrib.auth.models import Permission


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


def non_ajax_redir(*redir_args, **redir_kwargs):
    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def inner(request, *args, **kwargs):
            if not request.is_ajax():
                # we redirect you 
                return redirect(*redir_args, **redir_kwargs)
            return func(request, *args, **kwargs)

        return inner
    return decorator

def get_voting_fragments(initiative, request):
    context = dict(initiative=initiative, user_count=initiative.eligible_voter_count)
    add_vote_context(context, initiative, request)
    add_participation_count(context, initiative)

    return {'fragments': {
        '#voting': render_to_string("fragments/weighting.html" if initiative.is_plenumoptions() else
                                    "fragments/resistance.html" if initiative.is_contribution() else
                                    "fragments/voting.html",
                                    context=context,
                                    request=request),
        '#jump-to-vote': render_to_string("fragments/jump_to_vote.html",
                                    context=context)
        }}

def get_resistances_fragments(topic_id, request):
    context = get_topic_context(topic_id, request)
    context['evaluations'] = Initiative.objects.filter(topic=topic_id).filter(state='v').order_by('-went_to_discussion_at', '-went_public_at', '-created_at')
    return {'fragments': {
        '#voting': render_to_string("fragments/topic_resistances.html",
                                    context=context,
                                    request=request),
    }}

#
# ____    ____  __   ___________    __    ____   _______.
# \   \  /   / |  | |   ____\   \  /  \  /   /  /       |
#  \   \/   /  |  | |  |__   \   \/    \/   /  |   (----`
#   \      /   |  | |   __|   \            /    \   \    
#    \    /    |  | |  |____   \    /\    / .----)   |   
#     \__/     |__| |_______|   \__/  \__/  |_______/    
#
#                                                       

def process_weight_context(ctx):
    max_count = 0
    for option in ctx['options']:
        option['average'] = "%.1f" % (option['total'] / ctx['participation_count'])
        for count in option['counts']:
            max_count = max(max_count, count)
    ctx['max_count'] = max_count


def find_preferred_option(ctx):
    min_total = 10 * ctx['participation_count'] + 1
    for option in ctx['options']:
        if option['total'] < min_total:
            min_total = option['total']
            ctx['preferred_option'] = option['text']


def add_vote_context(ctx, init, request):

    preferences = get_preferences(request,init)
    if preferences.exists():
        ctx['preferences'] = preferences

    votes = init.votes.filter(user=request.user.id)
    if votes.exists():
        ctx['vote'] = votes.first()

    if init.is_contribution():
        resistance = init.resistances.filter(user=request.user.id)
        if resistance.exists():
            ctx ['resistance'] = resistance.get()

def get_topic_context(topic_id, request):
    context = {}
    context['topic'] = get_object_or_404(Topic, pk=topic_id)
    context['resistances'] = get_topic_resistances(request, topic_id).order_by('created_at')
    return context

def add_participation_count(ctx, init):
    ctx['participation_count'] = init.options.first().preferences.count() if init.options.exists() else init.votes.count()

def get_preferences(request,init):
    return Preference.objects.filter(option__initiative=init, user_id=request.user)

def get_resistance(request,init):
    return Resistance.objects.filter(contribution=init, user_id=request.user)

def get_topic_resistances(request, topic_id):
    return Resistance.objects.filter(contribution__topic=topic_id, user_id=request.user.id)

def personalize_argument(arg, user_id):
    arg.has_liked = arg.likes.filter(user=user_id).exists()
    arg.has_commented = arg.comments.filter(user__id=user_id).exists()

def ueber(request):
    return render(request, 'static/ueber.html',context=dict(
            quorums=Quorum.objects.order_by("-created_at")))


def index(request):
    filters = [f for f in request.GET.getlist("f")]
    if filters:
        request.session['init_filters'] = filters
    else:
        filters = request.session.get('init_filters', DEFAULT_FILTERS)

    inits = request.guard.make_intiatives_query(filters).prefetch_related("supporting")

    bereiche = [f for f in request.GET.getlist('b')]
    if bereiche:
        inits = inits.filter(bereich__in=bereiche)

    ids = [i for i in request.GET.getlist('id')]

    if ids:
        inits = inits.filter(id__in=ids)

    elif request.GET.get('s', None):
        searchstr = request.GET.get('s')

        if len(searchstr) >= settings.MIN_SEARCH_LENGTH:
            if connection.vendor == 'postgresql':
                inits = inits.annotate(search=SearchVector('title', 'subtitle','summary',
                        'problem', 'forderung', 'kosten', 'fin_vorschlag', 'arbeitsweise', 'init_argument')
                    ).filter(search=searchstr)
            else:
                inits = inits.filter(Q(title__icontains=searchstr) | Q(subtitle__icontains=searchstr))


    inits = sorted(inits, key=lambda x: x.sort_index or timedelta(days=1000))

    # now we filter for urgency


    if request.is_ajax():
        return render_to_json(
            {'fragments': {
                "#init-card-{}".format(init.id) : render_to_string("fragments/initiative/card.html",
                                                               context=dict(initiative=init),
                                                               request=request)
                    for init in inits },
             'inner-fragments': {
                '#init-list': render_to_string("fragments/initiative/list.html",
                                               context=dict(initiatives=inits),
                                               request=request)
             },
             # FIXME: ugly work-a-round as long as we use django-ajax
             #        for rendering - we have to pass it as a dict
             #        or it chokes on rendering :(
             'initiatives': json.loads(JSONRenderer().render(
                                SimpleInitiativeSerializer(inits, many=True).data,
                            ))
        }
)



    count_inbox = request.guard.make_intiatives_query(['i']).count()

    return render(request, 'initproc/index.html',context=dict(initiatives=inits,
                    inbox_count=count_inbox, filters=filters))



@login_required
def agora(request):
    open_topics = Topic.objects.exclude(closes_at__lt=timezone.now()).order_by('created_at')
    return render(request, 'initproc/agora.html',context=dict(topics=open_topics))


@login_required
def archive(request):
    archived_topics = Topic.objects.exclude(closes_at__gte=timezone.now()).order_by('created_at')
    return render(request, 'initproc/archive.html',context=dict(topics=archived_topics))


@login_required
def topic(request, topic_id, slug=None, archive=False):
    context = get_topic_context(topic_id, request)
    context['archive'] = archive
    contributions = Initiative.objects.filter(topic=topic_id)
    context['excavations'] = contributions.filter(state='c').order_by('-went_to_discussion_at', '-went_public_at', '-created_at')
    context['evaluations'] = contributions.filter(state='v').order_by('-went_to_discussion_at', '-went_public_at', '-created_at')
    context['discussions'] = contributions.filter(state='d').order_by('-went_to_discussion_at', '-went_public_at', '-created_at')
    context['reflections'] = contributions.filter(state='s').order_by('-went_public_at', '-created_at')
    context['initiations'] = contributions.filter(state='p', id__in=request.guard.initiated_initiatives()).order_by('-created_at')
    context['invitations'] = contributions.filter(state='p', id__in=request.guard.originally_supported_initiatives()).order_by('-created_at')

    topic = get_object_or_404(Topic, pk=topic_id)

    if context['excavations'].exists() and not topic.open_ended:
        context['participation_count'] = context['excavations'].first().resistances.count()
        context['options'] = sorted ([{
                "link": contribution,
                "text": contribution.title,
                "total": sum([resistance.value for resistance in contribution.resistances.all()]),
                "counts": [contribution.resistances.filter(value=i).count() for i in range(0, 11)],
                "reasons": contribution.resistances.exclude(reason='').order_by('value'),
                }
                for contribution in context['excavations'].all()],
                key=lambda x:x['total'])
        context['provide_reasons'] = any(option["reasons"].exists() for option in context['options'])
        process_weight_context(context)
    else:
        context['participation_count'] = 0

    return render(request, 'initproc/topic.html',context)

class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return get_user_model().objects.none()

        qs = get_user_model().objects.filter(is_active=True).all()

        if self.q:
            qs = qs.filter(Q(first_name__icontains=self.q) | Q(last_name__icontains=self.q) | Q(username__icontains=self.q))

        return qs

    def get_result_label(self, item):
        return render_to_string('fragments/autocomplete/user_item.html',
                                context=dict(user=item))

@login_required
def new(request):
    form = InitiativeForm()
    if request.method == 'POST':
        form = InitiativeForm(request.POST)
        if form.is_valid():
            ini = form.save(commit=False)
            with reversion.create_revision():
                ini.einordnung = VOTY_TYPES.Einzelinitiative
                ini.state = STATES.PREPARE
                ini.save()

                # Store some meta-information.
                reversion.set_user(request.user)
                if request.POST.get('commit_message', None):
                    reversion.set_comment(request.POST.get('commit_message'))


            Supporter(initiative=ini, user=request.user, initiator=True, ack=True, public=True).save()
            return redirect('/initiative/{}-{}'.format(ini.id, ini.slug))
        else:
            messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

    return render(request, 'initproc/new.html', context=dict(form=form,is_new=True))


@can_access_initiative()
def item(request, init, slug=None, initype=None):

    ctx = dict(initiative=init,
               user_count=init.eligible_voter_count,
               questions=[x for x in init.questions.prefetch_related('likes').all()],
               proposals=[x for x in init.proposals.prefetch_related('likes').all()],
               arguments=[x for x in init.pros.prefetch_related('likes').all()] +\
                         [x for x in init.contras.prefetch_related('likes').all()])

    ctx['arguments'].sort(key=lambda x: (-x.likes.count(), x.created_at))
    ctx['proposals'].sort(key=lambda x: (-x.likes.count(), x.created_at))
    ctx['questions'].sort(key=lambda x: (-x.likes.count(), x.created_at))
    ctx['is_editable'] = request.guard.is_editable (init)

    add_participation_count(ctx, init)

    if init.options.exists():
        if init.state == 'c':
            ctx['options'] = sorted ([{
                "text": option.text,
                "total": sum([preference.value for preference in option.preferences.all()]),
                "counts": [option.preferences.filter(value=i).count() for i in range(0, 11)]}
                for option in init.options.all()],
                key=lambda x:x['total'])
            process_weight_context(ctx)
            if init.options.count() <= 3:
                find_preferred_option(ctx)

    if request.user.is_authenticated:
        user_id = request.user.id

        ctx.update({'has_supported': init.supporting.filter(user=user_id).exists()})

        add_vote_context(ctx, init, request)

        for arg in ctx['arguments'] + ctx['proposals'] + ctx ['questions']:
            personalize_argument(arg, user_id)

    if init.is_contribution():
        if init.topic.open_ended and init.state == STATES.COMPLETED:
            ctx['participation_count'] = init.resistances.count()
            option={
                "total": sum([resistance.value for resistance in init.resistances.all()]),
                "counts": [init.resistances.filter(value=i).count() for i in range(0, 11)],
                "reasons": init.resistances.exclude(reason='').order_by('value'),
            }
            option['average'] = "%.1f" % (option['total'] / ctx['participation_count'])
            max_count = 0
            for count in option['counts']:
                max_count = max(max_count, count)
            ctx['max_count'] = max_count
            ctx['option'] = option
        return render(request, 'initproc/contribution.html', context=ctx)
    if init.is_policychange():
        return render(request, 'initproc/policychange.html', context=ctx)
    if init.is_plenumvote():
        return render(request, 'initproc/plenumvote.html', context=ctx)
    if init.is_plenumoptions():
        return render(request, 'initproc/plenumoptions.html', context=ctx)
    if init.is_initiative():
        return render(request, 'initproc/item.html', context=ctx)


@ajax
@can_access_initiative()
def show_resp(request, initiative, target_type, target_id, slug=None, initype=None):

    model_cls = apps.get_model('initproc', target_type)
    arg = get_object_or_404(model_cls, pk=target_id)

    assert arg.initiative == initiative, "How can this be?"

    ctx = dict(argument=arg,
               has_commented=False,
               is_editable=request.guard.is_editable(arg),
               full=param_as_bool(request.GET.get('full', 0)),
               comments=arg.comments.order_by('created_at').prefetch_related('likes').all())

    if request.user.is_authenticated:
        personalize_argument(arg, request.user.id)
        for cmt in ctx['comments']:
            cmt.has_liked = cmt.likes.filter(user=request.user).exists()

    template = 'fragments/argument/item.html'


    return {'fragments': {
        '#{arg.type}-{arg.id}'.format(arg=arg): render_to_string(template,
                                                                 context=ctx, request=request)
        }}

@ajax
@login_required
@can_access_initiative(None, 'can_moderate')
def show_moderation(request, initiative, target_id, slug=None, initype=None):
    arg = get_object_or_404(Moderation, pk=target_id)

    assert arg.initiative == initiative, "How can this be?"

    ctx = dict(m=arg,
               has_commented=False,
               has_liked=False,
               is_editable=True,
               full=1,
               comments=arg.comments.order_by('created_at').all())

    if request.user:
        ctx['has_liked'] = arg.likes.filter(user=request.user).exists()
        if arg.user == request.user:
            ctx['has_commented'] = True

    return {'fragments': {
        '#{arg.type}-{arg.id}'.format(arg=arg): render_to_string('fragments/moderation/item.html',
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
    is_post = request.method == 'POST'
    if initiative.is_initiative():
        form = InitiativeForm(request.POST or None, instance=initiative)
        if is_post:
            if form.is_valid():
                with reversion.create_revision():
                    initiative.save()

                    # Store some meta-information.
                    reversion.set_user(request.user)
                    if request.POST.get('commit_message', None):
                        reversion.set_comment(request.POST.get('commit_message'))

                initiative.supporting.filter(initiator=True).exclude(user=request.user).update(ack=False)

                messages.success(request, "Initiative gespeichert.")
                initiative.notify_followers(NOTIFICATIONS.INITIATIVE.EDITED, subject=request.user)
                return redirect('/initiative/{}'.format(initiative.id))
            else:
                messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

        return render(request, 'initproc/new.html', context=dict(form=form))
    elif initiative.is_policychange():
        form = PolicyChangeForm(request.POST or None, instance=initiative)
        if is_post:
            if form.is_valid():
                with reversion.create_revision():
                    initiative.save()

                    # Store some meta-information.
                    reversion.set_user(request.user)
                    if request.POST.get('commit_message', None):
                        reversion.set_comment(request.POST.get('commit_message'))

                messages.success(request, "AO-Änderung gespeichert.")
                # TODO fix pc.notify_followers(NOTIFICATIONS.INITIATIVE.EDITED, subject=request.user)
                return redirect('/{}/{}'.format(initiative.einordnung, initiative.id))
            else:
                messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

        return render(request, 'initproc/new_policychange.html', context=dict(form=form))
    elif initiative.is_plenumvote():
        form = PlenumVoteForm(request.POST or None, instance=initiative)
        if is_post:
            if form.is_valid():
                with reversion.create_revision():
                    initiative.save()

                    # Store some meta-information.
                    reversion.set_user(request.user)
                    if request.POST.get('commit_message', None):
                        reversion.set_comment(request.POST.get('commit_message'))

                messages.success(request, "Plenumsentscheidung gespeichert.")
                return redirect('/{}/{}'.format(initiative.einordnung, initiative.id))
            else:
                messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

        return render(request, 'initproc/new_plenumvote.html', context=dict(form=form))
    elif initiative.is_plenumoptions():
        options = {}
        if not is_post:
            for i in range (1,16): # TODO variable number of options
                options ['option{}'.format (i)] = initiative.options.get(index=i).text
        form = PlenumOptionsForm(request.POST or None, instance=initiative,initial=options)
        if is_post:
            if form.is_valid():
                with reversion.create_revision():
                    initiative.save()
                    for i in range (1,16): # TODO variable number of options
                        option = Option.objects.get (initiative=initiative,index=i)
                        option.text=form.data ['option{}'.format (i)]
                        option.save ()

                # Store some meta-information.
                    reversion.set_user(request.user)
                    if request.POST.get('commit_message', None):
                        reversion.set_comment(request.POST.get('commit_message'))

                messages.success(request, "Plenumsabwägung gespeichert.")
                return redirect('/{}/{}'.format(initiative.einordnung, initiative.id))
            else:
                messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

        return render(request, 'initproc/new_plenumoptions.html', context=dict(form=form))
    elif initiative.is_contribution():
        form = ContributionForm(request.POST or None, instance=initiative)
        if is_post:
            if form.is_valid():
                with reversion.create_revision():
                    initiative.save()

                    # Store some meta-information.
                    reversion.set_user(request.user)
                    if request.POST.get('commit_message', None):
                        reversion.set_comment(request.POST.get('commit_message'))

                messages.success(request, "Beitrag gespeichert.")
                # TODO fix pc.notify_followers(NOTIFICATIONS.INITIATIVE.EDITED, subject=request.user)
                return redirect('/{}/{}'.format(initiative.einordnung, initiative.id))
            else:
                messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

        return render(request, 'initproc/new_contribution.html', context=dict(form=form, topic=initiative.topic))


@login_required
@can_access_initiative([STATES.PREPARE, STATES.FINAL_EDIT], 'can_edit')
def submit_to_committee(request, initiative):
    if initiative.ready_for_next_stage:
        initiative.state = STATES.INCOMING if initiative.state == STATES.PREPARE else STATES.MODERATION
        initiative.save()

        # make sure moderation starts from the top
        initiative.moderations.update(stale=True)

        messages.success(request, "Deine Initiative wurde angenommen und wird geprüft.")
        initiative.notify_initiators(NOTIFICATIONS.INITIATIVE.SUBMITTED, subject=request.user)
        # To notify the review team, we notify all members of groups with moderation permission,
        # which doesn't include superusers, though they individually have moderation permission.
        moderation_permission = Permission.objects.filter(content_type__app_label='initproc', codename='add_moderation')
        initiative.notify(get_user_model().objects.filter(groups__permissions=moderation_permission, is_active=True).all(),
                          NOTIFICATIONS.INITIATIVE.SUBMITTED, subject=request.user)
        return redirect('/initiative/{}'.format(initiative.id))
    else:
        messages.warning(request, "Die Bedingungen für die Einreichung sind nicht erfüllt.")

    return redirect('/initiative/{}'.format(initiative.id))



@ajax
@login_required
@can_access_initiative(STATES.PREPARE, 'can_edit') 
@simple_form_verifier(InviteUsersForm, submit_title="Einladen")
def invite(request, form, initiative, invite_type):
    users = form.cleaned_data['user']
    for user in users:
        if user == request.user: continue # we skip ourselves
        if invite_type == 'initiators' and \
            initiative.supporting.filter(initiator=True).count() >= INITIATORS_COUNT:
            break

        try:
            supporting = initiative.supporting.get(user_id=user.id)
        except Supporter.DoesNotExist:
            supporting = Supporter(user=user, initiative=initiative, ack=False)

            if invite_type == 'initiators':
                supporting.initiator = True
            elif invite_type == 'supporters':
                supporting.first = True
        else:
            if invite_type == 'initiators' and not supporting.initiator:
                # we only allow promoting of supporters to initiators
                # not downwards.
                supporting.initiator = True
                supporting.first = False
                supporting.ack = False
            else:
                continue
        
        supporting.save()

        notify([user], NOTIFICATIONS.INVITE.SEND, {"target": initiative}, sender=request.user)

    if users.count():
        messages.success(request, ("Initiator*in" if invite_type == 'initiators' else 'Unterstützer*in') + ('nen' if users.count() > 1 else '') + ' eingeladen.')
    return redirect("/initiative/{}-{}".format(initiative.id, initiative.slug))



@login_required
@can_access_initiative(STATES.SEEKING_SUPPORT, 'can_support') # must be seeking supporters
def support(request, initiative):
    Supporter(initiative=initiative, user_id=request.user.id,
              public=not not request.GET.get("public", False)).save()

    if (initiative.is_contribution() and initiative.supporting.filter().count() >= initiative.quorum):
        initiative.state = STATES.DISCUSSION
        initiative.went_to_discussion_at = datetime.now()
        initiative.save()
        initiative.notify_followers(NOTIFICATIONS.INITIATIVE.WENT_TO_DISCUSSION)

    return redirect('/initiative/{}'.format(initiative.id))


@require_POST
@login_required
@can_access_initiative([STATES.PREPARE, STATES.INCOMING, STATES.FINAL_EDIT])
def ack_support(request, initiative):
    sup = get_object_or_404(Supporter, initiative=initiative, user_id=request.user.id)
    sup.ack = True
    sup.save()

    messages.success(request, "Danke für die Bestätigung")
    initiative.notify_initiators(NOTIFICATIONS.INVITE.ACCEPTED, subject=request.user)

    return redirect('/initiative/{}'.format(initiative.id))


@require_POST
@login_required
@can_access_initiative([STATES.SEEKING_SUPPORT, STATES.INCOMING, STATES.PREPARE])
def rm_support(request, initiative):
    sup = get_object_or_404(Supporter, initiative=initiative, user_id=request.user.id)
    sup.delete()

    messages.success(request, "Deine Unterstützung wurde zurückgezogen")
    initiative.notify_initiators(NOTIFICATIONS.INVITE.REJECTED, subject=request.user)

    if initiative.state == 's':
        return redirect('/initiative/{}'.format(initiative.id))
    return redirect('/')


@non_ajax_redir('/')
@ajax
@login_required
@can_access_initiative(STATES.DISCUSSION) # must be in discussion
@simple_form_verifier(NewArgumentForm, template="fragments/argument/new.html")
def new_argument(request, form, initiative):
    data = form.cleaned_data
    argCls = Pro if data['type'] == "👍" else Contra

    arg = argCls(initiative=initiative,
                 user_id=request.user.id,
                 title=data['title'],
                 text=data['text'])

    arg.save()

    initiative.notify_followers(NOTIFICATIONS.INITIATIVE.NEW_ARGUMENT, dict(argument=arg), subject=request.user)

    return {
        'fragments': {'#no-arguments': ""},
        'inner-fragments': {'#new-argument': render_to_string("fragments/argument/thumbs.html",
                                                  context=dict(initiative=initiative)),
                            '#debate-thanks': render_to_string("fragments/argument/argument_thanks.html"),
                            '#debate-count': initiative.pros.count() + initiative.contras.count()},
        'append-fragments': {'#argument-list': render_to_string("fragments/argument/item.html",
                                                  context=dict(argument=arg,full=0),
                                                  request=request)}
    }



@non_ajax_redir('/')
@ajax
@login_required
@can_access_initiative(STATES.DISCUSSION) # must be in discussion
@simple_form_verifier(NewProposalForm)
def new_proposal(request, form, initiative):
    data = form.cleaned_data
    proposal = Proposal(initiative=initiative,
                        user_id=request.user.id,
                        title=data['title'],
                        text=data['text'])

    proposal.save()

    return {
        'fragments': {'#no-proposals': ""},
        'inner-fragments': {'#new-proposal': render_to_string("fragments/argument/propose.html",
                                                  context=dict(initiative=initiative)),
                            '#proposals-thanks': render_to_string("fragments/argument/proposal_thanks.html"),
                            '#proposals-count': initiative.proposals.count()},
        'append-fragments': {'#proposal-list': render_to_string("fragments/argument/item.html",
                                                  context=dict(argument=proposal,full=0),
                                                  request=request)}
    }


@non_ajax_redir('/')
@ajax
@login_required
@can_access_initiative(STATES.DISCUSSION) # must be in discussion
@simple_form_verifier(NewQuestionForm)
def new_question(request, form, initiative):
    data = form.cleaned_data
    question = Question(initiative=initiative,
                        user_id=request.user.id,
                        title=data['title'],
                        text=data['text'])

    question.save()

    return {
        'fragments': {'#no-questions': ""},
        'inner-fragments': {'#new-question': render_to_string("fragments/argument/ask.html",
                                                              context=dict(initiative=initiative)),
                            '#questions-thanks': render_to_string("fragments/argument/question_thanks.html"),
                            '#questions-count': initiative.questions.count()},
        'append-fragments': {'#question-list': render_to_string("fragments/argument/item.html",
                                                                context=dict(argument=question,full=0),
                                                                request=request)}
    }


@ajax
@login_required
@can_access_initiative([STATES.INCOMING, STATES.MODERATION], 'can_moderate') # must be in discussion
@simple_form_verifier(NewModerationForm)
def moderate(request, form, initiative):
    model = form.save(commit=False)
    model.initiative = initiative
    model.user = request.user
    model.save()

    if request.guard.can_publish(initiative):
        if initiative.state == STATES.INCOMING:
            initiative.supporting.filter(ack=False).delete()
            initiative.went_public_at = datetime.now()
            initiative.state = STATES.SEEKING_SUPPORT
            initiative.save()

            messages.success(request, "Initiative veröffentlicht")
            initiative.notify_followers(NOTIFICATIONS.INITIATIVE.PUBLISHED)
            initiative.notify_moderators(NOTIFICATIONS.INITIATIVE.PUBLISHED, subject=request.user)
            return redirect('/initiative/{}'.format(initiative.id))

        elif initiative.state == STATES.MODERATION:

            publish = [initiative]
            if initiative.all_variants:
                # check the variants, too

                for ini in initiative.all_variants:
                    if ini.state != STATES.MODERATION or not request.guard.can_publish(ini):
                        publish = None
                        break
                    publish.append(ini)

            if publish:
                for init in publish:
                    init.went_to_voting_at = datetime.now()
                    init.state = STATES.VOTING
                    init.save()
                    init.notify_followers(NOTIFICATIONS.INITIATIVE.WENT_TO_VOTE)
                    init.notify_moderators(NOTIFICATIONS.INITIATIVE.WENT_TO_VOTE, subject=request.user)

                messages.success(request, "Initiative(n) zur Abstimmung frei gegeben.")
                return redirect('/initiative/{}-{}'.format(initiative.id, initiative.slug))


    
    return {
        'fragments': {'#no-moderations': ""},
        'inner-fragments': {'#moderation-new': "<strong>Eintrag aufgenommen</strong>"},
        'append-fragments': {'#moderation-list': render_to_string("fragments/moderation/item.html",
                                                  context=dict(m=model,initiative=initiative,full=0),
                                                  request=request)}
    }



@non_ajax_redir('/')
@ajax
@login_required
@simple_form_verifier(NewCommentForm)
def comment(request, form, target_type, target_id):
    model_cls = apps.get_model('initproc', target_type)
    model = get_object_or_404(model_cls, pk=target_id)

    if not request.guard.can_comment(model):
        raise PermissionDenied()


    data = form.cleaned_data
    cmt = Comment(target=model, user=request.user, **data)
    cmt.save()

    new_comment = "<strong>Danke für Deinen Kommentar</strong>";
    if (isinstance (model,Moderation)):
        new_comment += "<br>" + render_to_string("fragments/comment/button.html",context=dict(m=model))

    return {
        'inner-fragments': {'#{}-new-comment'.format(model.unique_id):
                new_comment,
                '#{}-chat-icon'.format(model.unique_id):
                "chat_bubble", # This user has now commented, so fill in the chat icon
                '#{}-comment-count'.format(model.unique_id):
                model.comments.count()},
        'append-fragments': {'#{}-comment-list'.format(model.unique_id):
            render_to_string("fragments/comment/item.html",
                             context=dict(comment=cmt),
                             request=request)}
    }


@non_ajax_redir('/')
@ajax
@login_required
def like(request, target_type, target_id):
    model_cls = apps.get_model('initproc', target_type)
    model = get_object_or_404(model_cls, pk=target_id)

    if not request.guard.can_like(model):
        raise PermissionDenied()

    if not request.guard.is_editable(model):
        raise PermissionDenied()

    ctx = {"target": model, "with_link": True, "show_text": False, "show_count": True, "has_liked": True, "is_editable": True}
    for key in ['show_text', 'show_count']:
        if key in request.GET:
            ctx[key] = param_as_bool(request.GET[key])

    Like(target=model, user=request.user).save()
    return {'fragments': {
        '.{}-like'.format(model.unique_id): render_to_string("fragments/like.html",
                                                             context=ctx,
                                                             request=request)
    }, 'inner-fragments': {
        '.{}-like-icon'.format(model.unique_id): 'favorite',
        '.{}-like-count'.format(model.unique_id): model.likes.count(),
    }}


@non_ajax_redir('/')
@ajax
@login_required
def unlike(request, target_type, target_id):
    model_cls = apps.get_model('initproc', target_type)
    model = get_object_or_404(model_cls, pk=target_id)

    if not request.guard.is_editable(model):
        raise PermissionDenied()

    model.likes.filter(user_id=request.user.id).delete()

    ctx = {"target": model, "with_link": True, "show_text": False, "show_count": True, "has_liked": False, "is_editable": True}
    for key in ['show_text', 'show_count']:
        if key in request.GET:
            ctx[key] = param_as_bool(request.GET[key])

    return {'fragments': {
        '.{}-like'.format(model.unique_id): render_to_string("fragments/like.html",
                                                             context=ctx,
                                                             request=request)
    }, 'inner-fragments': {
        '.{}-like-icon'.format(model.unique_id): 'favorite_border',
        '.{}-like-count'.format(model.unique_id): model.likes.count(),
    }}



@non_ajax_redir('/')
@ajax
@login_required
@require_POST
@can_access_initiative(STATES.VOTING) # must be in voting
def vote(request, init):
    voted_value = request.POST.get('voted')
    if voted_value == 'no':
        voted = VOTED.NO
    elif voted_value == "yes":
        voted = VOTED.YES
    else:
        voted = VOTED.ABSTAIN


    reason = request.POST.get("reason", "")
    try:
        my_vote = Vote.objects.get(initiative=init, user_id=request.user)
    except Vote.DoesNotExist:
        my_vote = Vote(initiative=init, user_id=request.user.id, value=voted)
    else:
        my_vote.voted = voted
        my_vote.reason = reason
    my_vote.save()

    return get_voting_fragments(init, request)

@non_ajax_redir('/')
@ajax
@login_required
@require_POST
@can_access_initiative(STATES.VOTING) # must be in voting
def preference(request, init):
    preferences = get_preferences(request, init)
    preferences_existed = preferences.exists()
    for option in init.options.all():
        value = request.POST.get('option{}'.format(option.index))
        if preferences_existed:
            my_preference = preferences.get(option=option)
            my_preference.value = value
        else:
            my_preference = Preference(option=option, user_id=request.user.id, value=value)
        my_preference.save()

    return get_voting_fragments(init, request)

@non_ajax_redir('/')
@ajax
@login_required
@require_POST
@can_access_initiative(STATES.DISCUSSION) # must be in discussion
def resistance(request, init):
    resistance = get_resistance(request, init)
    value = request.POST.get('option')
    if resistance.exists():
        my_resistance = resistance.get()
        my_resistance.value = value
    else:
        my_resistance = Resistance(contribution=init, user_id=request.user.id, value=value)
    my_resistance.reason = request.POST.get('reason')
    my_resistance.save()

    return get_voting_fragments(init, request)


@non_ajax_redir('/')
@ajax
@login_required
@require_POST
def topic_resistances(request, topic_id, slug):
    contributions = Initiative.objects.filter(topic=topic_id, state='v').order_by('-went_to_discussion_at', '-went_public_at', '-created_at')
    resistances = get_topic_resistances(request, topic_id)

    resistances_existed = resistances.exists()
    for contribution in contributions:
        value = request.POST.get('contribution{}'.format(contribution.id))
        reason = request.POST.get('reason{}'.format(contribution.id))
        if resistances_existed:
            my_resistance = resistances.get(contribution=contribution)
            my_resistance.value = value
            my_resistance.reason = reason
        else:
            my_resistance = Resistance(contribution=contribution, user_id=request.user.id, value=value, reason=reason)
        my_resistance.save()

    return get_resistances_fragments(topic_id, request)

@non_ajax_redir('/')
@ajax
@can_access_initiative()
def compare(request, initiative, version_id):
    versions = Version.objects.get_for_object(initiative)
    latest = versions.first()
    selected = versions.filter(id=version_id).first()
    compare = {key: mark_safe(html_diff(selected.field_dict.get(key, ''),
                                        latest.field_dict.get(key, '')))
            for key in COMPARING_FIELDS}

    compare['went_public_at'] = initiative.went_public_at


    return {
        'inner-fragments': {
            'header': "",
            '.main': render_to_string("fragments/compare.html",
                                      context=dict(initiative=initiative,
                                                    selected=selected,
                                                    latest=latest,
                                                    compare=compare),
                                      request=request)}
    }



@non_ajax_redir('/')
@ajax
@login_required
@require_POST
@can_access_initiative(STATES.VOTING) # must be in voting
def reset_vote(request, init):
    Vote.objects.filter(initiative=init, user_id=request.user).delete()
    return get_voting_fragments(init, request)

@non_ajax_redir('/')
@ajax
@login_required
@require_POST
@can_access_initiative(STATES.VOTING) # must be in voting
def reset_preference(request, init):
    get_preferences(request, init).delete()
    return get_voting_fragments(init, request)

@non_ajax_redir('/')
@ajax
@login_required
@require_POST
@can_access_initiative(STATES.DISCUSSION) # must be in discussion
def reset_resistance(request, init):
    get_resistance(request, init).delete()
    return get_voting_fragments(init, request)

@non_ajax_redir('/')
@ajax
@login_required
@require_POST
def reset_topic_resistances(request, topic_id, slug):
    get_topic_resistances(request, topic_id).delete()
    return get_resistances_fragments(topic_id, request)

# See §9 (2) AO
@login_required
def new_policychange(request):
    if not request.guard.can_create_policy_change():
        raise PermissionDenied()

    form = PolicyChangeForm()
    if request.method == 'POST':
        form = PolicyChangeForm(request.POST)
        if form.is_valid():
            pc = form.save(commit=False)
            with reversion.create_revision():
                pc.state = STATES.PREPARE
                pc.einordnung = VOTY_TYPES.PolicyChange
                pc.save()

                # Store some meta-information.
                reversion.set_user(request.user)
                if request.POST.get('commit_message', None):
                    reversion.set_comment(request.POST.get('commit_message'))

                # all board members are initiators of a policy change
                for initiator in get_user_model().objects.filter(groups__name=BOARD_GROUP, is_active=True):
                    Supporter(initiative=pc, user=initiator, initiator=True, ack=True, public=True).save()

            return redirect('/{}/{}-{}'.format(pc.einordnung, pc.id, pc.slug))
        else:
            messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

    return render(request, 'initproc/new_policychange.html', context=dict(form=form, is_new=True))

# This is only used for policy changes; the policy change goes directly from preparation to discussion; see §9 (2) AO
@login_required
@can_access_initiative([STATES.PREPARE], 'can_edit')
def start_discussion_phase(request, init):
    if init.ready_for_next_stage:
        init.state = STATES.DISCUSSION
        init.went_public_at = datetime.now()
        init.went_to_discussion_at = datetime.now()

        init.save()
        # TODO fix notify_followers(NOTIFICATIONS.INITIATIVE.WENT_TO_DISCUSSION)
        return redirect('/{}/{}'.format(init.einordnung, init.id))
    else:
        messages.warning(request, "Die Bedingungen für die Einreichung sind nicht erfüllt.")

    return redirect('/{}/{}'.format(init.einordnung, init.id))

# This is only used for contributions; the contribution goes directly from preparation to seeking support, or to discussion if it already has enough support
@login_required
@can_access_initiative([STATES.PREPARE], 'can_edit')
def start_support_phase(request, init):
    if init.ready_for_next_stage:
        # In this case, this doesn't really mean "public", just published for logged-in users
        init.went_public_at = datetime.now()
        init.supporting.filter(ack=False).delete()
        init.state = STATES.DISCUSSION if init.supporting.count() >= init.quorum else STATES.SEEKING_SUPPORT
        init.save()
        return redirect('/{}/{}'.format(init.einordnung, init.id))
    else:
        messages.warning(request, "Die Bedingungen für die Einreichung sind nicht erfüllt.")

    return redirect('/{}/{}'.format(init.einordnung, init.id))
@login_required
def new_plenumvote(request):
    if not request.guard.can_create_plenum_vote():
        raise PermissionDenied()

    form = PlenumVoteForm()
    if request.method == 'POST':
        form = PlenumVoteForm(request.POST)
        if form.is_valid():
            pv = form.save(commit=False)
            with reversion.create_revision():
                pv.state = STATES.PREPARE
                pv.einordnung = VOTY_TYPES.PlenumVote
                pv.save()

                # Store some meta-information.
                reversion.set_user(request.user)
                if request.POST.get('commit_message', None):
                    reversion.set_comment(request.POST.get('commit_message'))

                # all board members are initiators of a plenum vote
                for initiator in get_user_model().objects.filter(groups__name=BOARD_GROUP, is_active=True):
                    Supporter(initiative=pv, user=initiator, initiator=True, ack=True, public=True).save()

            return redirect('/{}/{}-{}'.format(pv.einordnung, pv.id, pv.slug))
        else:
            messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

    return render(request, 'initproc/new_plenumvote.html', context=dict(form=form, is_new=True))

@login_required
def new_plenumoptions(request):
    if not request.guard.can_create_plenum_vote():
        raise PermissionDenied()

    form = PlenumOptionsForm()
    if request.method == 'POST':
        form = PlenumOptionsForm(request.POST)
        if form.is_valid():
            pv = form.save(commit=False)
            with reversion.create_revision():
                pv.state = STATES.PREPARE
                pv.einordnung = VOTY_TYPES.PlenumOptions
                pv.save()

                for i in range (1,16): # TODO variable number of options
                    Option(initiative=pv,text=form.data ['option{}'.format (i)],index=i).save()

                # Store some meta-information.
                reversion.set_user(request.user)
                if request.POST.get('commit_message', None):
                    reversion.set_comment(request.POST.get('commit_message'))

                # all board members are initiators of a plenum vote
                for initiator in get_user_model().objects.filter(groups__name=BOARD_GROUP, is_active=True):
                    Supporter(initiative=pv, user=initiator, initiator=True, ack=True, public=True).save()

            return redirect('/{}/{}-{}'.format(pv.einordnung, pv.id, pv.slug))
        else:
            messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

    return render(request, 'initproc/new_plenumoptions.html', context=dict(form=form, is_new=True))

# This is only used for plenum votes; the plenum vote goes directly from preparation to voting
@login_required
@can_access_initiative([STATES.PREPARE], 'can_edit')
def start_voting(request, init):
    if (init.is_plenumvote or init.is_plenumoptions) and init.ready_for_next_stage:
        init.went_public_at = datetime.now()
        init.went_to_voting_at = datetime.now()
        init.state = STATES.VOTING
        init.save()
        # TODO fix notify_followers(NOTIFICATIONS.INITIATIVE.WENT_TO_VOTE)
        return redirect('/{}/{}'.format(init.einordnung, init.id))
    else:
        messages.warning(request, "Die Bedingungen für die Veröffentlichung sind nicht erfüllt.")

    return redirect('/{}/{}'.format(init.einordnung, init.id))

@login_required
def new_contribution(request, topic_id, slug=None):
    if not request.guard.can_create_contribution():
        raise PermissionDenied()

    topic = get_object_or_404(Topic, pk=topic_id)

    form = ContributionForm()
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            with reversion.create_revision():
                contribution.state = STATES.PREPARE
                contribution.einordnung = VOTY_TYPES.Contribution
                contribution.topic = topic
                contribution.save()

                # Store some meta-information.
                reversion.set_user(request.user)
                if request.POST.get('commit_message', None):
                    reversion.set_comment(request.POST.get('commit_message'))

                Supporter(initiative=contribution, user=request.user, initiator=True, ack=True, public=True).save()

            return redirect('/{}/{}-{}'.format(contribution.einordnung, contribution.id, contribution.slug))
        else:
            messages.warning(request, "Bitte korrigiere die folgenden Probleme:")

    return render(request, 'initproc/new_contribution.html', context=dict(form=form, topic=topic, is_new=True))
