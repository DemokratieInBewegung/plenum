from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q
from dal import autocomplete
from django import forms

from .helpers import notify_initiative_listeners
from .models import (Initiative, Argument, Comment, Vote, Supporter, Like)
# Create your views here.

DEFAULT_FILTERS = ['s', 'd', 'v']
STAFF_ONLY = ['i', 'm', 'h']

def ensure_state(state):
    def wrap(fn):
        def view(request, init_id, *args, **kwargs):
            init = get_object_or_404(Initiative, pk=init_id)
            assert init.state == state, "Not in expected state: {}".format(state)
            return fn(request, init, *args, **kwargs)
        return view
    return wrap


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
            count_inbox = Initiative.objects.filter(Q(state='i') and (
                Q(initiators__id=request.user.id) |
                Q(supporters__user_id=request.user.id, supporters__first=True))
            ).count()
            if 'i' in request.GET.getlist("f"):
                inits = Initiative.objects.filter(Q(state__in=filters) | (Q(state='i') and (
                    Q(initiators__id=request.user.id) |
                    Q(supporters__user_id=request.user.id, supporters__first=True))))
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
    print(value)
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
            "subtitle": "Teaser",
            "summary" : "Zusammenfassung",
            "problem": "Problembeschreibung",
            "fordering" : "Forderung",
            "kosten": "Kosten",
            "fin_vorschlag": "Finanzierungsvorschlag",
            "arbeitsweise": "Arbeitsweise",
            "init_argument": "Argument der Initiator/innen",
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
            form.save_m2m()
            ini.initiators.add(request.user.id)

            for uid in form.cleaned_data['supporters'].all():
                if uid in ini.initiators.all(): continue # you can only be one
                Supporter(initiative=ini, user=uid, first=True, public=True).save()


            notify_initiative_listeners(ini, "wurde eingereicht.")
            messages.success(request, "Deine Initiative wurde angenommen und wir geprüft.")
            return redirect('/')
        else:
            messages.warning(request, "Bitte korrigiere die folgenden Probleme:")
            
    return render(request, 'initproc/new.html', context=dict(form=form))


def item(request, init_id):
    init = get_object_or_404(Initiative, pk=init_id)
    if init.state in STAFF_ONLY:
        if not request.user.is_authenticated:
            raise PermissionDenied()
        if not request.user.is_staff and \
           not init.initiators.filter(id=request.user.id) and \
           not init.supporters.filter(user_id=request.user.id, first=True):
            raise PermissionDenied()

    ctx = dict(initiative=init, pro=[], contra=[],
               arguments=init.arguments.prefetch_related("comments").prefetch_related("likes").all())

    for arg in ctx['arguments']:
        ctx["pro" if arg.in_favor else "contra"].append(arg)

    ctx['pro'].sort(key=lambda x: x.likes.count(), reverse=True)
    ctx['contra'].sort(key=lambda x: x.likes.count(), reverse=True)

    if request.user.is_authenticated:
        user_id = request.user.id
        ctx.update({'has_supported': init.supporters.filter(user=user_id).count(),
                    'has_demanded_vote': 0,
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


# actions

@require_POST
@login_required
@ensure_state('s') # must be seeking for supporters
def support(request, initiative):
    Supporter(initiative=initiative, user_id=request.user.id,
              public=not not request.POST.get("public", False)).save()

    return redirect('/initiative/{}'.format(initiative.id))



@require_POST
@login_required
@ensure_state('d') # must be in discussion
def post_argument(request, initiative):
    Argument(initiative=initiative, user_id=request.user.id,
             text=request.POST.get('text', ''),
             title=request.POST.get('title', ''),
             in_favor=request.POST.get('vote', 'yay') != 'nay').save()

    return redirect('/initiative/{}'.format(initiative.id))

@require_POST
@login_required
@ensure_state('d') # must be in discussion
def post_comment(request, init, arg_id):
    argument = get_object_or_404(Argument, pk=arg_id)
    assert init.id == argument.initiative.id, "Argument doesn't belong to Initiative"

    Comment(argument=argument, user_id=request.user.id,
             text=request.POST.get('text', '')).save()

    return redirect('/initiative/{}#argument-{}'.format(init.id, argument.id))

@require_POST
@login_required
@ensure_state('d') # must be in discussion
def like_argument(request, init, arg_id):
    argument = get_object_or_404(Argument, pk=arg_id)
    assert init.id == argument.initiative.id, "Argument doesn't belong to Initiative"

    Like(argument=argument, user_id=request.user.id).save()

    return redirect('/initiative/{}#argument-{}'.format(init.id, argument.id))

@require_POST
@login_required
@ensure_state('d') # must be in discussion
def unlike_argument(request, init, arg_id):
    argument = get_object_or_404(Argument, pk=arg_id)
    assert init.id == argument.initiative.id, "Argument doesn't belong to Initiative"

    like = Like.objects.get(argument=arg_id, user_id=request.user.id)
    if like:
        like.delete()

    return redirect('/initiative/{}#argument-{}'.format(init.id, argument.id))



@require_POST
@login_required
@ensure_state('v') # must be in voting
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