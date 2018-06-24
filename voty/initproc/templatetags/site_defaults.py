"""
================================================================================
Expose site specific parameters set in .ini file
================================================================================
"""

# parameters   (* default)
# ------------------------------------------------------------------------------

# https://docs.djangoproject.com/en/2.0/howto/custom-template-tags/
# https://docs.djangoproject.com/en/dev/topics/settings/#custom-default-settings
# call: {% load site_defaults %} then call {% getSiteSetting parameter %}

import os
from django.conf import settings
from django import template
from django.template.defaultfilters import stringfilter
from six.moves import configparser

site_parser = configparser.ConfigParser()
site_parser.read(os.path.join(settings.BASE_DIR, "init.ini"))

register = template.Library()

# WORKS
#@register.simple_tag
#def get_setting(my_setting):
#  return site_parser.get("settings", my_setting)

# {{ variable|filter-foo:"argument" }}  filter foo is passed variable and argument
# {{ SETTING|get_setting }}
@register.filter
@stringfilter
def get_setting(my_setting=None):
  if my_setting == '':
    return "XXX-missing-setting-XXX"
  return site_parser.get("settings", my_setting)
