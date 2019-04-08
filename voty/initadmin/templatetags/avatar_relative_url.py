from avatar.templatetags.avatar_tags import avatar_url
from avatar.utils import cache_result
from django import template
from django.conf import settings

register = template.Library()

@cache_result()
@register.simple_tag(takes_context=True)
def avatar_relative_url(context, user, size=settings.AVATAR_DEFAULT_SIZE):
	return avatar_url(user, size)
