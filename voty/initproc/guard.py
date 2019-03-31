"""
The Single one place, where all permissions are defined
"""
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q

from functools import wraps
from voty.initadmin.models import UserConfig
from voty.initproc.models import Moderation
from .globals import STATES, PUBLIC_STATES, TEAM_ONLY_STATES, INITIATORS_COUNT, MINIMUM_MODERATOR_VOTES, \
    MINIMUM_FEMALE_MODERATOR_VOTES, MINIMUM_DIVERSE_MODERATOR_VOTES, VOTY_TYPES, BOARD_GROUP
from .models import Initiative, Supporter


def can_access_initiative(states=None, check=None):
    def wrap(fn):
        def view(request, initype, init_id, slug, *args, **kwargs):
            init = get_object_or_404(Initiative, pk=init_id)
            if states:
                assert init.state in states, "{} Not in expected state: {}".format(init.state, states)
            if  not request.guard.can_view(init):
                raise PermissionDenied()

            if check:
                if not getattr(request.guard, check)(init):
                    raise PermissionDenied()

            request.initiative = init
            return fn(request, init, *args, **kwargs)
        return view
    return wrap

class ContinueChecking(Exception): pass

def _compound_action(func):
    @wraps(func)
    def wrapped(self, obj=None, *args, **kwargs):
        if obj is None: # if none given, fall back to the initiative of the request
            obj = self.request.initiative
        try:
            return getattr(self, "_{}_{}".format(func.__name__, obj._meta.model_name))(obj, *args, **kwargs)
        except (AttributeError, ContinueChecking):
            return func(self, obj)
    return wrapped


class Guard:
    """
    An instance of the guard for the given user
    """
    def __init__(self, user, request=None):
        self.user = user
        self.request = request
        # REASON IS NOT THREAD SAFE, but works good enough for us
        # for now.
        self.reason = None

    def initiated_initiatives(self):
        return Supporter.objects.filter(initiator=True, user_id=self.user.id).values('initiative_id')

    def originally_supported_initiatives(self):
        return Supporter.objects.filter(first=True, user_id=self.user.id).values('initiative_id')

    def always_visible_initiatives(self):
        return Supporter.objects.filter(Q(first=True) | Q(initiator=True), user_id=self.user.id).values('initiative_id')

    def make_intiatives_query(self, filters):
        if not self.user.is_authenticated:
            filters = [f for f in filters if f in PUBLIC_STATES]
        elif not self.user.has_perm('initproc.add_moderation'):
            filters = [f for f in filters if f not in TEAM_ONLY_STATES]

        if self.user.is_authenticated and not self.user.has_perm('initproc.add_moderation'):
            return Initiative.objects.filter(Q(topic=None) & (Q(state__in=filters) | Q(state__in=TEAM_ONLY_STATES,
                                                                                       id__in=self.always_visible_initiatives())))

        return Initiative.objects.filter(topic=None, state__in=filters)

    @_compound_action
    def can_comment(self, obj=None):
        if (isinstance (obj,Moderation)):
            return True

        self.reason = None
        latest_comment = obj.comments.order_by("-created_at").first()

        if not latest_comment and obj.user == self.user:
            self.reason = "Erst wenn eine Person Dein Argument kommentiert hat, kannst Du dieses ebenfalls kommentieren."
            return False
        elif latest_comment and latest_comment.user == self.user:
            self.reason = "Im Sinne einer abwechslungsreichen Diskussion kannst Du dieses Argument erst nach einer anderen Person wieder kommentieren."
            return False

        return True

    def can_like(self, obj=None):
        if obj.user == self.user: # should apply for both arguments and comments
            return False

        return True

    def is_editable(self, obj=None): #likes
        initiative = self.find_parent_initiative(obj)
        if initiative and initiative.state in [STATES.COMPLETED, STATES.ACCEPTED, STATES.REJECTED]: # no liking of closed inis
            return False
        return True

    def find_parent_initiative(self, obj=None):
        # find initiative in object tree
        while not hasattr(obj, "initiative") and hasattr(obj, "target"):
            obj = obj.target
        return obj.initiative if hasattr(obj, "initiative") else obj

    def is_initiator(self, init):
        return init.supporting.filter(initiator=True, user_id=self.user.id)

    def is_supporting(self, init):
        return init.supporting.filter(user_id=self.user.id)

    def my_vote(self, init):
        return init.options.first().preferences.filter(user=self.user.id).exists() if init.options.exists() else init.votes.filter(user=self.user.id).first()

    @_compound_action
    def can_view(self, obj=None):
        # fallback if compound doesn't match
        return False

    @_compound_action
    def can_edit(self, obj=None):
        # fallback if compound doesn't match
        return False

    @_compound_action
    def can_publish(self, obj=None):
        # fallback if compound doesn't match
        return False

    @_compound_action
    def can_support(self, obj=None):
        # fallback if compound doesn't match
        return False

    @_compound_action
    def can_moderate(self, obj=None):
        # fallback if compound doesn't match
        return False


    # 
    #    INITIATIVES
    #    -----------
    # 

    # how many (female, diverse, total) moderators are missing?
    def _mods_missing_for_i(self, init):
        female  = MINIMUM_FEMALE_MODERATOR_VOTES
        diverse = MINIMUM_DIVERSE_MODERATOR_VOTES
        total   = MINIMUM_MODERATOR_VOTES

        moderations = init.moderations.filter(stale=False)

        total -= moderations.count()

        for config in UserConfig.objects.filter(user_id__in=moderations.values("user_id")):
            if config.is_female_mod:
                female -= 1
            if config.is_diverse_mod:
                diverse -= 1

        return (female, diverse, total)

    def can_inivite_initiators(self, init=None):
        init = init or self.request.initiative
        if init.state != STATES.PREPARE:
            return False

        if not self._can_edit_initiative(init):
            return False

        return init.supporting.filter(initiator=True).count() < INITIATORS_COUNT


    def should_moderate_initiative(self, init=None):
        init = init or self.request.initiative
        if not self._can_moderate_initiative(init):
            return False

        moderations = init.moderations.filter(stale=False)

        if moderations.filter(user=self.user):
            # has already voted, thanks, bye
            return False

        (female,diverse,total) = self._mods_missing_for_i(init)

        try:
            if female > 0:
                if self.user.config.is_female_mod:
                    return True

            if diverse > 0:
                if self.user.config.is_diverse_mod:
                    return True
        except User.config.RelatedObjectDoesNotExist:
            pass

        # user cannot contribute to fulfilling quota -- should moderate unless we already know it'll be wasted
        return (total > female) & (total > diverse)

    def userIsBoard(self):
        return self.user.groups.filter(name=BOARD_GROUP).exists()

    def can_create_policy_change(self, init=None):
        return self.userIsBoard()

    def can_create_plenum_vote(self, init=None):
        return self.userIsBoard()

    def can_create_contribution(self, init=None):
        return self.user.is_authenticated

    ## compounds

    def _can_view_initiative(self, init):
        if init.is_contribution and not self.user.is_authenticated:
            return False

        if init.state not in TEAM_ONLY_STATES:
            return True

        if not self.user.is_authenticated:
            return False

        if self.user.has_perm('initproc.add_moderation') or \
           init.supporting.filter(Q(first=True) | Q(initiator=True), user_id=self.request.user.id):
            return True

        return False

    def _can_edit_initiative(self, init):
        if not init.state in [STATES.PREPARE, STATES.FINAL_EDIT]:
            return False
        if not self.user.is_authenticated:
            return False
        if self.user.is_superuser:
            return True
        if init.supporting.filter(initiator=True, user_id=self.request.user.id):
            return True

        return False

    def _can_publish_initiative(self, init):
        if not self.user.has_perm('initproc.add_moderation'):
            return False

        if init.supporting.filter(ack=True, initiator=True).count() != INITIATORS_COUNT:
            return False

        if init.moderations.filter(stale=False, vote='n'): # We have NAYs
            return False

        (female,diverse,total) = self._mods_missing_for_i(init)

        return (female <= 0) & (diverse <= 0) & (total <= 0)

    def _can_support_initiative(self, init):
        return (init.is_initiative() or init.is_contribution()) and \
               init.state == STATES.SEEKING_SUPPORT and \
               self.user.is_authenticated

    def _can_moderate_initiative(self, init):
        if init.is_initiative():
            if init.state in [STATES.INCOMING, STATES.MODERATION] and self.user.has_perm('initproc.add_moderation'):
                if init.supporting.filter(user=self.user, initiator=True):
                    self.reason = "Als Mitinitator*in darfst Du nicht mit moderieren."
                    return False
                return True
        return False

    def _can_comment_pro(self, obj=None):
        if obj.initiative.state == STATES.DISCUSSION:
            raise ContinueChecking()
        return False

    def _can_comment_contra(self, obj=None):
        if obj.initiative.state == STATES.DISCUSSION:
            raise ContinueChecking()
        return False

    def _can_comment_proposal(self, obj=None):
        if obj.initiative.state == STATES.DISCUSSION:
            raise ContinueChecking()
        return False


def add_guard(get_response):
    """
    Add the guard of the `request.user` to it and make it accessible directly at `request.guard`
    """
    def middleware(request):
        guard = Guard(request.user, request)
        request.guard = guard
        request.user.guard = guard

        # record user's last activity
        if request.method == 'POST' and request.user.is_authenticated and request.path != '/account/logout/':
            request.user.config.act()

        response = get_response(request)
        return response

    return middleware
