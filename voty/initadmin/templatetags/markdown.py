from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.html import urlize

import markdown2
import bleach

register = template.Library()

@register.filter(name="markdown")
def markdown(text):
    text = markdown2.markdown(urlize(text, nofollow=True, autoescape=True))
    html = bleach.clean(text, tags=settings.MARKDOWN_FILTER_WHITELIST_TAGS)
    return mark_safe(bleach.linkify(html))

register.filter('markdown', markdown)