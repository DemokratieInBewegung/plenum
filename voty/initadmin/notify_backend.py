from django.utils.translation import ugettext
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from pinax.notifications.backends.base import BaseBackend
from notifications.signals import notify


class SiteBackend(BaseBackend):
    spam_sensitivity = 0
    
    def deliver(self, recipient, sender, notice_type, extra_context):
        notify_kw = {
          "verb": notice_type.label
        }
        for x in ['action_object', 'target', 'verb', 'description']:
          if x in extra_context:
            notify_kw[x] = extra_context[x]

        notify.send(sender, recipient=recipient, **notify_kw)



def mark_as_read(get_response):
    """
    Mark all notifications related to the initiative of the given request
    as read
    """
    def middleware(request):
        # from voty.initproc.models import Initiative
        response = get_response(request)
        if request.user and request.user.is_authenticated:
            if getattr(request, 'initiative', None):
              init_type = ContentType.objects.get_for_model(request.initiative)
              q = request.user.notifications.filter(
                  Q(actor_content_type=init_type, actor_object_id=request.initiative.id) | \
                  Q(target_content_type=init_type, target_object_id=request.initiative.id)).mark_all_as_read()
            if getattr(request, 'issue', None):
              issue = ContentType.objects.get_for_model(request.issue)
              q = request.user.notifications.filter(
                  Q(actor_content_type=issue, actor_object_id=request.issue.id) | \
                  Q(target_content_type=issue, target_object_id=request.issue.id)).mark_all_as_read()
            if getattr(request, 'solution', None):
              solution = ContentType.objects.get_for_model(request.solution)
              q = request.user.notifications.filter(
                  Q(actor_content_type=solution, actor_object_id=request.solution.id) | \
                  Q(target_content_type=solution, target_object_id=request.solution.id)).mark_all_as_read()

        return response

    return middleware
