import datetime
from django import template

register = template.Library()

class Guard(template.Node):

    def __init__(self, parser, token):
        try:
            # Splitting by None == splitting by spaces.
            tag_name, arg, obj = token.contents.split(None, 2)
        except ValueError:
            try:
                # Splitting by None == splitting by spaces.
                tag_name, arg = token.contents.split(None, 1)
                obj = None
            except ValueError:
                raise template.TemplateSyntaxError(
                    "%r tag requires at least the function on the guard" % token.contents.split()[0]
                )
        self.method = arg
        self.obj = obj

    def render(self, context):
        if hasattr(context['user'], 'guard'):
            obj = context[self.obj] if self.obj else None
            context[self.method] = getattr(context['user'].guard, self.method)(obj)
        return ''



register.tag("guard", Guard)