from django.contrib import admin
from .models import Initiative, Quorum, Supporter, Argument, Comment, Vote


class InitiativeAdmin(admin.ModelAdmin):
    list_display = ['title', 'state', 'created_at', 'changed_at']
    ordering = ['title', 'created_at', 'changed_at']
    # actions = ['move_on', 'send_invite', 'decline']
    search_fields = ['title', 'summary']


admin.site.register(Initiative, InitiativeAdmin)
admin.site.register(Quorum)
admin.site.register(Supporter)
admin.site.register(Argument)
admin.site.register(Comment)
admin.site.register(Vote)