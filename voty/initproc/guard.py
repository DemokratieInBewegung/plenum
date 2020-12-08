"""
The Single one place, where all permissions are defined
"""
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db.models.signals import post_save, post_delete
from django.utils import timezone

from functools import wraps
from voty.initadmin.models import UserConfig
from voty.initproc.models import Moderation
from .globals import STATES, PUBLIC_STATES, TEAM_ONLY_STATES, INITIATORS_COUNT, MINIMUM_MODERATOR_VOTES, \
    MINIMUM_FEMALE_MODERATOR_VOTES, MINIMUM_DIVERSE_MODERATOR_VOTES, BOARD_GROUP, MINIMUM_REVIEW_TEAM_SIZE
from .models import Initiative, Issue, Solution, Supporter
from django.contrib import messages
from math import ceil
from math import floor


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
    
def can_access_issue(statuses=None, check=None):
    def wrap(fn):
        def view(request, issue_id, slug, *args, **kwargs):
            issue = get_object_or_404(Issue, pk=issue_id)
            if statuses:
                assert issue.status in statuses, "{} Not in expected status: {}".format(issue.status, statuses)
            if  not request.guard.can_view(issue):
                raise PermissionDenied()

            if check:
                if not getattr(request.guard, check)(issue) and (not(issue.went_to_review_at and not issue.went_to_seeking_support_at) or check != 'can_moderate'):
                    raise PermissionDenied()

            request.issue = issue
            return fn(request, issue, *args, **kwargs)
        return view
    return wrap
    
def can_access_solution(statuses=None, check=None):
    def wrap(fn):
        def view(request, solution_id, slug, *args, **kwargs):
            solution = get_object_or_404(Solution, pk=solution_id)
            if statuses:
                assert solution.status in statuses, "{} Not in expected status: {}".format(solution.status, statuses)
            if  not request.guard.can_view(solution):
                raise PermissionDenied()

            if check:
                if not getattr(request.guard, check)(solution) and (solution.status != 'r' or check != 'can_moderate'):
                    raise PermissionDenied()

            request.solution = solution
            return fn(request, solution, *args, **kwargs)
        return view
    return wrap

class ContinueChecking(Exception): pass

def _compound_action(func):
    @wraps(func)
    def wrapped(self, obj=None, *args, **kwargs):
        if obj is None: # if none given, fall back to the initiative of the request
            if hasattr(self.request,'initiative'):
                obj = self.request.initiative
            if hasattr(self.request,'issue'):
                obj = self.request.issue
            if hasattr(self.request,'solution'):
                obj = self.request.solution
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
        
    # how many (female, diverse, total) reviewers are missing?
    # min MINIMUM_REVIEW_TEAM_SIZE teammates have to be in group
    # min 50% of all votes must be female for a valid result
    # min 25% of alle votes must be diverse for a valid result
    def _mods_missing_for_issue(self, issue):
        review_permission = Permission.objects.filter(content_type__app_label='initproc', codename='add_review')
        teamsize = get_user_model().objects.filter(groups__permissions=review_permission, is_active=True).count()
        if teamsize < MINIMUM_REVIEW_TEAM_SIZE:
            return (0, 0, -1) # this is an error
        
        reqyesvotes = floor(teamsize/2)+1
        sufnovotes = ceil(teamsize/2)

        moderations = issue.issuemoderations.filter(stale=False)
        yesvotessofar = moderations.filter(vote='y').count()
        novotessofar = moderations.filter(vote='n').count()
        votessofar = yesvotessofar + novotessofar
        
        # (min) number of remaining required votes:
        total = min((reqyesvotes - yesvotessofar), (sufnovotes - novotessofar))
        if total <= 0:
            return (0, 0, 0)
            
        # (min) count of votes for a valid result
        all_votes = votessofar+total
        
        female_votes = 0
        diverse_votes = 0
        for config in UserConfig.objects.filter(user_id__in=moderations.values("user_id")):
            if config.is_female_mod:
                female_votes += 1
            if config.is_diverse_mod:
                diverse_votes += 1
                
        female = max(0, ceil(all_votes / 2) - female_votes)
        diverse = max(0, ceil(all_votes / 4) - diverse_votes)

        return (female, diverse, total)
        
        
    # how many (female, diverse, total) reviewers are missing?
    # min MINIMUM_REVIEW_TEAM_SIZE teammates have to be in group
    # min 50% of all votes must be female for a valid result
    # min 25% of alle votes must be diverse for a valid result
    def _mods_missing_for_solution(self, solution):
        review_permission = Permission.objects.filter(content_type__app_label='initproc', codename='add_review')
        teamsize = get_user_model().objects.filter(groups__permissions=review_permission, is_active=True).count()
        if teamsize < MINIMUM_REVIEW_TEAM_SIZE:
            return (0, 0, -1) # this is an error
        
        reqyesvotes = floor(teamsize/2)+1
        sufnovotes = ceil(teamsize/2)

        moderations = solution.moderationslist.filter(stale=False)
        yesvotessofar = moderations.filter(vote='y').count()
        novotessofar = moderations.filter(vote='n').count()
        votessofar = yesvotessofar + novotessofar
        
        # (min) number of remaining required votes:
        total = min((reqyesvotes - yesvotessofar), (sufnovotes - novotessofar))
        if total <= 0:
            return (0, 0, 0)
            
        # (min) count of votes for a valid result
        all_votes = votessofar+total
        
        female_votes = 0
        diverse_votes = 0
        for config in UserConfig.objects.filter(user_id__in=moderations.values("user_id")):
            if config.is_female_mod:
                female_votes += 1
            if config.is_diverse_mod:
                diverse_votes += 1
                
        female = max(0, ceil(all_votes / 2) - female_votes)
        diverse = max(0, ceil(all_votes / 4) - diverse_votes)

        return (female, diverse, total)
        

    def can_inivite_initiators(self, init=None):
        init = init or self.request.initiative
        if init.state != STATES.PREPARE:
            return False

        if not self._can_edit_initiative(init):
            return False

        return init.supporting.filter(initiator=True).count() < INITIATORS_COUNT
        
    def can_inivite_issue_initiators(self, issue=None):
        issue = issue or self.request.issue
        if issue.status != STATES.PREPARE:
            return False

        if not self._can_edit_issue(issue):
            return False

        return issue.supporters.filter(initiator=True).count() < INITIATORS_COUNT


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
        
        
    def has_reviewed_issue(self, issue=None):
        issue = issue or self.request.issue
        moderations = issue.issuemoderations.filter(stale=False)
        if moderations.filter(user=self.user):
            return True
        return False
            
    def should_moderate_issue(self, issue=None):
        issue = issue or self.request.issue
        if not self._can_moderate_issue(issue):
            return False

        moderations = issue.issuemoderations.filter(stale=False)

        if moderations.filter(user=self.user):
            # has already voted, thanks, bye
            return False

        (female,diverse,total) = self._mods_missing_for_issue(issue)
        
        if total <= 0:
            if total == -1:
                messages.error(self.request, "Das Prüfteam ist zu klein")
            return False
        
        isfemale = False
        isdiverse = False
        try:
            if self.user.config.is_female_mod:
                isfemale = True
        except User.config.RelatedObjectDoesNotExist:
            pass

        try:
            if self.user.config.is_diverse_mod:
                isdiverse = True
        except User.config.RelatedObjectDoesNotExist:
            pass
        
        if female > 0:
            if isfemale:
                if total > diverse or isdiverse: # if diverses are yet required, we need a female diverse person
                    return True

        if diverse > 0:
            if isdiverse:
                if total > female or isfemale: # if females are yet required, we need a female diverse person
                    return True

        # user cannot contribute to fulfilling quota -- should moderate unless we already know it'll be wasted
        self.reason = "Um die Quoten zu erfüllen, muss zuerst noch eine Frau* oder eine Vielfaltsperson prüfen."
        return (total > female) & (total > diverse)
        
        
    def has_reviewed_solution(self, solution=None):
        solution = solution or self.request.solution
        moderations = solution.moderationslist.filter(stale=False)
        if moderations.filter(user=self.user):
            return True
        return False
    
    def should_moderate_solution(self, solution=None):
        solution = solution or self.request.solution
        if not self._can_moderate_solution(solution):
            return False

        moderations = solution.moderationslist.filter(stale=False)

        if moderations.filter(user=self.user):
            # has already voted, thanks, bye
            return False

        (female,diverse,total) = self._mods_missing_for_solution(solution)
        
        if total <= 0:
            if total == -1:
                messages.error(self.request, "Das Prüfteam ist zu klein")
            return False
        
        isfemale = False
        isdiverse = False
        try:
            if self.user.config.is_female_mod:
                isfemale = True
        except User.config.RelatedObjectDoesNotExist:
            pass

        try:
            if self.user.config.is_diverse_mod:
                isdiverse = True
        except User.config.RelatedObjectDoesNotExist:
            pass
        
        if female > 0:
            if isfemale:
                if total > diverse or isdiverse: # if diverses are yet required, we need a female diverse person
                    return True

        if diverse > 0:
            if isdiverse:
                if total > female or isfemale: # if females are yet required, we need a female diverse person
                    return True

        # user cannot contribute to fulfilling quota -- should moderate unless we already know it'll be wasted
        self.reason = "Um die Quoten zu erfüllen, muss zuerst noch eine Frau* oder eine Vielfaltsperson prüfen."
        return (total > female) & (total > diverse)
        

    def userIsBoard(self):
        return self.user.groups.filter(name=BOARD_GROUP).exists()

    def can_create_policy_change(self, init=None):
        return self.userIsBoard()

    def can_create_plenum_vote(self, init=None):
        return self.userIsBoard()

    def can_create_contribution(self, init=None):
        return self.user.is_authenticated

    def can_create_solution(self, solution=None):
        return self.user.is_authenticated

    ## compounds

    def _can_view_initiative(self, init):
        if init.is_contribution() and not self.user.is_authenticated:
            return False

        if init.state not in TEAM_ONLY_STATES:
            return True

        if not self.user.is_authenticated:
            return False

        if self.user.has_perm('initproc.add_moderation') or \
           init.supporting.filter(Q(first=True) | Q(initiator=True), user_id=self.request.user.id):
            return True

        return False

    def _can_view_issue(self, issue):
        if not self.user.is_authenticated:
            return False
            
        if issue.status == STATES.PREPARE and not issue.supporters.filter(initiator=True, user_id=self.request.user.id) and not self.user.has_perm('initproc.add_review'):#in Agora Liste unsichtbar, Einzelansicht aber für Agora Prüfteam zugelassen, um Hilfestellung während Vorbereitung bieten zu können
            return False
            
        return True #jeder darf in jedem Status sehen, sofern angemeldet, außer nicht selbst (mit)initiierte in Vorbereitung befindliche Fragestellungen
        """

        if issue.status not in TEAM_ONLY_STATES:
            return True

        if self.user.has_perm('initproc.add_review') or issue.supporters.filter(Q(first=True) | Q(initiator=True), user_id=self.request.user.id):
            return True

        return False
        """

    def _can_view_solution(self, solution):
        if not self.user.is_authenticated:
            return False
            
        return True

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

    def _can_edit_issue(self, issue):
        if not issue.status in [STATES.PREPARE, STATES.INCOMING]:
            return False
        if not self.user.is_authenticated:
            return False
        if issue.status == STATES.PREPARE and self.user.is_superuser:
            return True
        if issue.status == STATES.INCOMING and self._can_moderate_issue(issue):
            return True
        if issue.status == STATES.PREPARE and issue.supporters.filter(initiator=True, ack=True, user_id=self.request.user.id):
            return True

        return False

    def _can_edit_solution(self, solution):
        if not self.user.is_authenticated:
            return False
        if self.user.is_superuser:
            return True
        if self._can_moderate_solution(solution):
            return True
        if solution.status == STATES.DISCUSSION and not solution.has_arguments and not solution.current_moderations and solution.user.id == self.request.user.id:
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

    def _can_publish_issue(self, issue):
        if not self.user.has_perm('initproc.add_review'):
            return False

        if issue.supporters.filter(ack=True, initiator=True).count() != INITIATORS_COUNT:
            return False

        (female,diverse,total) = self._mods_missing_for_issue(issue)

        return (total == 0)

    def _can_publish_solution(self, solution):
        if not self.user.has_perm('initproc.add_review'):
            return False

        (female,diverse,total) = self._mods_missing_for_solution(solution)

        return (total == 0)

    def _can_support_initiative(self, init):
        return (init.is_initiative() or init.is_contribution()) and \
               init.state == STATES.SEEKING_SUPPORT and \
               self.user.is_authenticated

    def _can_support_issue(self, issue):
        return issue.status == STATES.SEEKING_SUPPORT and self.user.is_authenticated

    def _can_moderate_initiative(self, init):
        if init.is_initiative():
            if init.state in [STATES.INCOMING, STATES.MODERATION] and self.user.has_perm('initproc.add_moderation'):
                if init.supporting.filter(user=self.user, initiator=True):
                    self.reason = "Als Mitinitator*in darfst Du nicht mit moderieren."
                    return False
                return True
        return False

    def _can_moderate_issue(self, issue):
        if issue.status in [STATES.INCOMING, STATES.MODERATION] and self.user.has_perm('initproc.add_review'):
            if issue.supporters.filter(user=self.user, initiator=True):
                self.reason = "Als Mitinitator*in darfst Du nicht mit moderieren."
                return False
            return True
        return False

    def _can_moderate_solution(self, solution):
        if self.user.has_perm('initproc.add_review'):
            if solution.issue.supporters.filter(user=self.user, initiator=True):
                self.reason = "Als Mitinitator*in darfst Du nicht mit moderieren."
                return False
            if solution.user == self.user:
                self.reason = "Als Ersteller darfst Du nicht mit moderieren."
                return False
            return True
        return False

    def can_vote_issue(self):
        if self.user.config.is_party_member:
            return True
        else:
            self.reason = "Nur Parteimitglieder dürfen abstimmen"
        return False

    def is_moderation_leader(self, init=None):
        return (self.user.has_perm('initproc.add_moderation') and self.user.has_perm('initproc.is_group_leader'))

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

        def create_config(instance, created, **kwargs):
            if created:
                UserConfig.objects.get_or_create(user=instance)

        post_save.connect(create_config, sender=User)

        guard.changed = False

        if request.user.is_authenticated and not request.path.startswith('/account/log') and not request.path.startswith('/admin'):
            def change(**kwargs):
                guard.changed = True

            post_delete.connect(change)
            post_save.connect(change)

        response = get_response(request)

        if guard.changed:
            request.user.config.last_activity = timezone.now()
            request.user.config.save()

        return response

    return middleware
