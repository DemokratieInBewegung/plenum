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

from .apps import InitprocConfig
from .helpers import notify_initiative_listeners
from .models import (Initiative, Pro, Contra, Proposal, Comment, Vote, Quorum, Supporter, Like, INITIATORS_COUNT)
from .forms import NewArgumentForm, NewCommentForm
# Create your views here.

DEFAULT_FILTERS = ['s', 'd', 'v']
STAFF_ONLY = ['i', 'm', 'h']


def can_access_initiative(states=None):
    def wrap(fn):
        def view(request, init_id, slug, *args, **kwargs):
            init = get_object_or_404(Initiative, pk=init_id)
            if states:
                assert init.state in states, "Not in expected state: {}".format(state)
            if init.state in STAFF_ONLY:
                if not request.user.is_authenticated:
                    raise PermissionDenied()
                if not request.user.is_staff and \
                   not init.supporting.filter(Q(first=True) | Q(initiator=True), user_id=request.user.id):
                    raise PermissionDenied()

            return fn(request, init, *args, **kwargs)
        return view
    return wrap


def simple_form_verifier(form_cls, template="fragments/simple_form.html", via_ajax=True,
                         submit_klasses="btn-outline-primary", submit_title="Abschicken"):
    def wrap(fn):
        def view(request, *args, **kwargs):
            if request.method == "POST":
                form = form_cls(request.POST)
                if form.is_valid():
                    return fn(request, form, *args, **kwargs)
            else:
                form = form_cls()

            fragment = request.GET.get('fragment')
            rendered = render_to_string(template,
                        context=dict(fragment=fragment, form=form, ajax=via_ajax,
                                     submit_klasses=submit_klasses,
                                     submit_title=submit_title),
                        request=request)
            if fragment:
                return {'inner-fragments': {fragment: rendered}}
            return rendered
        return view
    return wrap



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
    filters = request.GET.getlist("f") or DEFAULT_FILTERS
    count_inbox = 0
    if not request.user or not request.user.is_staff:
        # state i is only available to staff
        filters = [f for f in filters if f not in STAFF_ONLY]


    inits = Initiative.objects.filter(state__in=filters)

    if request.user.is_authenticated:
        if request.user.is_staff:
            count_inbox = Initiative.objects.filter(state='i').count()
        else:
            count_inbox = Initiative.objects.filter(
                    Q(supporting__first=True) | Q(supporting__initiator=True),
                    state='i',
                    supporting__user_id=request.user.id
            ).count()
            if 'i' in request.GET.getlist("f"):
                inits = Initiative.objects.filter(Q(state__in=filters) | Q(
                        Q(supporting__first=True) | Q(supporting__initiator=True),
                        state='i',
                        supporting__user_id=request.user.id))
                filters.append('i')


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


def has_enough_initiators(value):
    if len(value) != 2:
        raise ValidationError("Du brauchst genau zwei Mitinitiator/innen!")


class NewInitiative(forms.ModelForm):

    supporters = forms.ModelMultipleChoiceField(
        label="Erstunterstützer/innen",
        queryset=get_user_model().objects,
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
                    url='user_autocomplete',
                    attrs={"data-placeholder": "Zum Suchen tippen"}))


    initiators = forms.ModelMultipleChoiceField(
        label="Mitinitiator/innen",
        help_text="Hier gibst Du an welche Beweger/innen diese Initiative mit Dir einbringen. Jede Initiative muss von drei Beweger/innen eingebracht werden.",
        queryset=get_user_model().objects,
        validators=[has_enough_initiators],
        widget=autocomplete.ModelSelect2Multiple(
                    url='user_autocomplete',
                    attrs={"data-placeholder": "Zum Suchen tippen"}))
    class Meta:
        model = Initiative
        fields = ['title', 'subtitle', 'initiators', 'summary', 'problem', 'forderung',
                  'kosten', 'fin_vorschlag', 'arbeitsweise', 'init_argument',
                  'einordnung', 'ebene', 'bereich']

        labels = {
            "title" : "Überschrift",
            "subtitle": "Anreizer",
            "summary" : "Zusammenfassung",
            "problem": "Problembeschreibung",
            "forderung" : "Forderung",
            "kosten": "Kosten",
            "fin_vorschlag": "Finanzierungsvorschlag",
            "arbeitsweise": "Arbeitsweise",
            "init_argument": "Argument der Initiator/innen",
        }
        help_texts = {
            "title" : "Die Überschrift sollte kurz und knackig eure Forderung enthalten.",
            "subtitle": "Hier reißt ihr kurz das Problem an, welches eure Initiative lösen soll. Versucht es auf 1-2 Sätze zu beschränken.",
            "summary" : "Hier schreibt bitte 3-4 Sätze, die zusammenfassen, worum es in dieser Initiative geht.",
            "problem": "Hier bitte in 3-4 Sätze das Problem beschreiben, dass ihr mit eurer Initiative lösen wollt.",
            "forderung" : "Was sind eure konkrete Forderungen?",
            "kosten": "Entstehen Kosten für Eure Initiative? Versucht bitte, wenn möglich, eine ungefähre Einschätzung über die Höhe der Kosten zu geben.ten",
            "fin_vorschlag": "Hier solltet ihr kurz erklären, wie die Kosten gedeckt werden könnten. Hier reicht auch zu schreiben, dass die Initiative über Steuereinnahmen finanziert wird.",
            "arbeitsweise": "Habt ihr mit Expert/innen gesprochen? Wo kommen eure Informationen her? Hier könnt ihr auch Quellen angeben.",
            "init_argument": "Hier dürft ihr emotional werden: Warum ist euch das wichtig und warum bringt ihr diese Initiative ein?",

        }


@login_required
def new(request):
    form = NewInitiative()
    if request.method == 'POST':
        form = NewInitiative(request.POST)
        if form.is_valid():
            ini = form.save(commit=False)
            ini.state = Initiative.STATES.INCOMING
            ini.save()

            Supporter(initiative=ini, user=request.user, initiator=True, ack=True, public=True).save()

            for uid in form.cleaned_data['initiators'].all():
                Supporter(initiative=ini, user=uid, initiator=True, ack=False, public=True).save()

            for uid in form.cleaned_data['supporters'].all():
                if uid in ini.supporters.all(): continue # you can only be one
                Supporter(initiative=ini, user=uid, initiator=False, first=True, public=True).save()


            notify_initiative_listeners(ini, "wurde eingereicht.")
            messages.success(request, "Deine Initiative wurde angenommen und wird geprüft.")
            return redirect('/')
        else:
            messages.warning(request, "Bitte korrigiere die folgenden Probleme:")
            
    return render(request, 'initproc/new.html', context=dict(form=form))


@can_access_initiative()
def item(request, init, slug=None):

    ctx = dict(initiative=init,
               show_proposals=request.GET.get('show_proposals', False),
               arguments=[x for x in init.pros.prefetch_related('likes').all()] +\
                         [x for x in init.contras.prefetch_related('likes').all()])
    ctx['arguments'].sort(key=lambda x: (x.likes.count(), x.created_at), reverse=True)

    if request.user.is_authenticated:
        user_id = request.user.id
        ctx.update({'has_supported': init.supporting.filter(user=user_id).count(),
                    'has_voted': init.votes.filter(user=user_id).count()})
        if ctx['has_voted']:
            ctx['vote'] = init.votes.filter(user=user_id).first().vote

        if ctx['arguments']:
            for arg in ctx['arguments']:
                arg.has_liked = arg.likes.filter(user=user_id).count() > 0
                if arg.user.id == user_id:
                    arg.has_commented = True
                else:
                    for cmt in arg.comments:
                        if cmt.user.id == user_id:
                            arg.has_commented = True
                            break

    return render(request, 'initproc/item.html', context=ctx)


@ajax
@can_access_initiative()
def show_argument(request, initiative, arg_type, arg_id, slug=None):

    arg = get_object_or_404(Pro if arg_type == 'pro' else Contra, pk=arg_id)
    assert arg.initiative == initiative, "How can this be?"

    ctx = dict(argument=arg,
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
        '#{arg.type}-{arg.id}'.format(arg=arg): render_to_string('fragments/argument/full.html',
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


@require_POST
@login_required
@can_access_initiative('s') # must be seeking for supporters
def support(request, initiative):
    Supporter(initiative=initiative, user_id=request.user.id,
              public=not not request.POST.get("public", False)).save()

    return redirect('/initiative/{}'.format(initiative.id))


@require_POST
@login_required
@user_passes_test(lambda u: u.is_staff)
@can_access_initiative(Initiative.STATES.INCOMING) # must be unpublished
def publish(request, initiative):
    if initiative.supporting.filter(ack=True, initiator=True).count() != INITIATORS_COUNT:
        messages.error(request, "Nicht genügend Initiatoren haben bestätigt")
        return redirect('/initiative/{}'.format(initiative.id))


    # clean out unknown 
    initiative.supporting.filter(ack=False).delete()
    initiative.went_public_at = datetime.now()
    initiative.state = Initiative.STATES.SEEKING_SUPPORT
    initiative.save()

    messages.success(request, "Initiative veröffentlicht")

    # FIXME: notifications would be cool.

    return redirect('/initiative/{}'.format(initiative.id))


@require_POST
@login_required
@can_access_initiative('i')
def ack_support(request, initiative):
    sup = get_object_or_404(Supporter, initiative=initiative, user_id=request.user.id)
    sup.ack = True
    sup.save()

    messages.success(request, "Danke für die Bestätigung")

    return redirect('/initiative/{}'.format(initiative.id))


@require_POST
@login_required
@can_access_initiative(['s', 'i'])
def rm_support(request, initiative):
    sup = get_object_or_404(Supporter, initiative=initiative, user_id=request.user.id)
    sup.delete()

    messages.success(request, "Deine Unterstützung wurde zurückgezogen")

    if initiative.state == 's':
        return redirect('/initiative/{}'.format(initiative.id))
    return redirect('/')



@ajax
@login_required
@can_access_initiative('d') # must be in discussion
@simple_form_verifier(NewArgumentForm)
def new_argument(request, form, initiative):
    data = form.cleaned_data
    argCls = Pro if data['type'] == "👍" else Contra

    arg = argCls(initiative=initiative,
                 user_id=request.user.id,
                 title=data['title'],
                 text=data['title'])

    arg.save()

    return {
        'inner-fragments': {'#new-argument': "<strong>Danke für dein Argument</strong>"},
        'append-fragments': {'#argument-list': render_to_string("fragments/argument/small.html",
                                                  context=dict(argument=arg),
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

    Like(target=model, user=request.user).save()
    return {'fragments': {
        '#{}-like'.format(model.unique_id): render_to_string("fragments/like.html",
                                                             context=dict(has_liked=True, target=model),
                                                             request=request)
    }}


@ajax
@login_required
def unlike(request, target_type, target_id):
    model_cls = apps.get_model('initproc', target_type)
    model = get_object_or_404(model_cls, pk=target_id)

    model.likes.filter(user_id=request.user.id).delete()

    return {'fragments': {
        '#{}-like'.format(model.unique_id): render_to_string("fragments/like.html",
                                                             context=dict(has_liked=False, target=model),
                                                             request=request)
    }}



@require_POST
@login_required
@can_access_initiative('v') # must be in voting
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