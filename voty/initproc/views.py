from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Initiative, Argument, Comment, Vote, Supporter, DemandingVote
# Create your views here.

def ensure_state(state):
    def wrap(fn):
        def view(request, init_id, *args, **kwargs):
            init = get_object_or_404(Initiative, pk=init_id)
            assert init.state == state, "Not in expected state: {}".format(state)
            return fn(request, init, *args, **kwargs)
        return view
    return wrap


def index(request):
    inits = Initiative.objects.all()
    return render(request, 'initproc/index.html', context=dict(initiatives=inits))


def item(request, init_id):
    init = get_object_or_404(Initiative, pk=init_id)
    ctx = dict(initiative=init, pro=[], contra=[],
               arguments=init.arguments.prefetch_related("comments").all())

    for arg in ctx['arguments']:
        ctx["pro" if arg.in_favor else "contra"].append(arg)

    if request.user.is_authenticated:
        user_id = request.user.id
        ctx.update({'has_supported': init.supporters.filter(user=user_id).count(),
                    'has_demanded_vote': init.demands.filter(user=user_id).count(),
                    'has_voted': init.votes.filter(user=user_id).count()})
        if ctx['has_voted']:
            ctx['vote'] = init.votes.filter(user=user_id).first().vote

        if ctx['arguments']:
            for arg in ctx['arguments']:
                if arg.user.id == user_id:
                    arg.has_commented = True
                else:
                    for cmt in arg.comments:
                        if arg.user.id == user_id:
                            arg.has_commented = True
                            break

    return render(request, 'initproc/item.html', context=ctx)


# actions

@require_POST
@login_required
@ensure_state('n') # must be new
def support(request, initiative):
    print(request.user.id)
    Supporter(initiative=initiative, user_id=request.user.id,
              public=not not request.POST.get("public", False)).save()

    return redirect('/initiative/{}'.format(initiative.id))


@require_POST
@login_required
@ensure_state('d') # must be new
def demand_vote(request, initiative):
    DemandingVote(initiative=initiative, user_id=request.user.id,
              public=not not request.POST.get("public", False)).save()

    return redirect('/initiative/{}'.format(initiative.id))


@require_POST
@login_required
@ensure_state('d') # must be i discussion
def post_argument(request, initiative):
    Argument(initiative=initiative, user_id=request.user.id,
             text=request.POST.get('text', ''),
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