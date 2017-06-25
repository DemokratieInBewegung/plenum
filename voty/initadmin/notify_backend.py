from django.utils.translation import ugettext

from pinax.notifications.backends.base import BaseBackend
from notifications.signals import notify

class SiteBackend(BaseBackend):
    spam_sensitivity = 0
    
    def deliver(self, recipient, sender, notice_type, extra_context):
        context = self.default_context()
        context.update({
          "recipient": recipient,
          "sender": sender,
          "notice": ugettext(notice_type.display),  
        })
        context.update(extra_context)
        messages = self.get_formatted_messages(("notice.html",),
            notice_type.label, context)

        notify_kw = {
          "verb": notice_type.label,
          "description": messages["notice.html"]
        }
        for x in ['action_object', 'target', 'verb', 'description']:
          if x in extra_context:
            notify_kw[x] = extra_context[x]

        notify.send(sender, recipient=recipient, **notify_kw)

