"""
The Single one place, where all permissions are defined
"""
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q

from functools import wraps
from voty.initadmin.models import UserConfig
from .models import Initiative, INITIATORS_COUNT

PUBLIC_STATES = [Initiative.STATES.SEEKING_SUPPORT,
                 Initiative.STATES.DISCUSSION,
                 Initiative.STATES.FINAL_EDIT,
                 Initiative.STATES.VOTING,
                 Initiative.STATES.ACCEPTED,
                 Initiative.STATES.REJECTED]

STAFF_ONLY_STATES = [Initiative.STATES.INCOMING,
                     Initiative.STATES.MODERATION,
                     Initiative.STATES.HIDDEN]


def can_access_initiative(states=None, check=None):
    def wrap(fn):
        def view(request, init_id, slug, *args, **kwargs):
            init = get_object_or_404(Initiative, pk=init_id)
            if states:
                assert init.state in states, "Not in expected state: {}".format(state)
            if  not request.guard.can_view(init):
                raise PermissionDenied()

            if check:
                if not getattr(request.guard, check)(init):
                    raise PermissionDenied()

            request.initiative = init

            return fn(request, init, *args, **kwargs)
        return view
    return wrap



def _compound_action(func):
    @wraps(func)
    def wrapped(self, obj=None, *args, **kwargs):
        if obj is None: # if none given, fall back to the initiative of the request
            obj = self.request.initiative
        try:
            return getattr(self, "_{}_{}".format(func.__name__, obj._meta.model_name))(obj, *args, **kwargs)
        except AttributeError:
            return func(obj)
    return wrapped


class Guard:
    """
    An instance of the guard for the given user
    """
    def __init__(self, user, request=None):
        self.user = user
        self.request = request

    def make_intiatives_query(self, filters):
        if not self.user.is_authenticated:
            filters = [f for f in filters if f in PUBLIC_STATES]
        elif not self.user.is_staff:
            filters = [f for f in filters if f not in STAFF_ONLY_STATES]

        if self.user.is_authenticated and not self.user.is_staff:
            return Initiative.objects.filter(Q(state__in=filters) | Q(
                    Q(supporting__first=True) | Q(supporting__initiator=True),
                    state__in=STAFF_ONLY_STATES,
                    supporting__user_id=self.user.id))

        return Initiative.objects.filter(state__in=filters)


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

    def _mod_counts_for_i(self, init):

        has_female = has_diversity = has_enough = False
        for count, config in enumerate(UserConfig.objects.filter(user_id__in=init.moderations.filter(stale=False).values("user_id"))):
            if config.is_female_mod:
                has_female = True
            if config.is_diverse_mod:
                has_diversity = False

            if c >= 3:
                has_enough = True

        return (has_female, has_diversity, has_enough)

    def can_inivite_initiators(self, init=None):
        init = init or self.request.initiative
        if init.state != Initiative.STATES.PREPARE:
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

        (has_female, has_diversity, has_enough) = self._mod_counts_for_i(init)

        try:
            if not has_female:
                if self.user.config.is_female_mod:
                    return True

            if not has_diversity:
                if self.user.config.is_diverse_mod:
                    return True
        except User.config.RelatedObjectDoesNotExist:
            pass

        return not has_enough

    ## compounds

    def _can_view_initiative(self, init):
        if init.state not in STAFF_ONLY_STATES:
            return True

        if not self.user.is_authenticated:
            return False

        if not self.user.is_staff and \
           not init.supporting.filter(Q(first=True) | Q(initiator=True), user_id=self.request.user.id):
            return False

        return True

    def _can_edit_initiative(self, init):
        if not init.state in [Initiative.STATES.PREPARE, Initiative.STATES.FINAL_EDIT]:
            return False
        if not self.user.is_authenticated:
            return False
        if not init.supporting.filter(Q(first=True) | Q(initiator=True), user_id=self.request.user.id):
            return False

        return True

    def _can_publish_initiative(self, init):
        if not self.user.is_staff:
            return False

        if init.supporting.filter(ack=True, initiator=True).count() != INITIATORS_COUNT:
            return False

        if init.moderations.filter(stale=False, vote='n'): # We have NAYs
            return False

        return self._mod_counts_for_i(init) == (True, True, True)

    def _can_support_initiative(self, init):
        return init.state == Initiative.STATES.SEEKING_SUPPORT and self.user.is_authenticated

    def _can_moderate_initiative(self, init):
        return init.state == Initiative.STATES.INCOMING and self.user.is_staff


def add_guard(get_response):
    """
    Add the guard of the `request.user` to it and make it accessible directly at `request.guard`
    """
    def middleware(request):
        guard = Guard(request.user, request)
        request.guard = guard
        request.user.guard = guard

        response = get_response(request)
        return response

    return middleware
