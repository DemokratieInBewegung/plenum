from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

import markdown2
import bleach

register = template.Library()

@register.filter
def markdown(text):
    text = markdown2.markdown(text)
    html = bleach.clean(text, tags=settings.MARKDOWN_FILTER_WHITELIST_TAGS)
    return mark_safe(bleach.linkify(html))
