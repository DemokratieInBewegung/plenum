from avatar.templatetags.avatar_tags import avatar_url
from django.contrib.sites.models import Site
from avatar.utils import cache_result
from django import template
from django.conf import settings

register = template.Library()

@cache_result()
@register.simple_tag(takes_context=True)
def avatar_full_url(context, user, size=settings.AVATAR_DEFAULT_SIZE):
	url = avatar_url(user, size)
	if url.startswith("http"):
		return url
	return context.request.build_absolute_uri(url)