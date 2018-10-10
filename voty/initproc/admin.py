from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Initiative, Quorum, Supporter, Pro, Contra, Proposal, Comment, Vote, Moderation, Option, Preference

class InitiativeAdmin(VersionAdmin):
    list_display = ['einordnung', 'title', 'state', 'created_at', 'changed_at']
    ordering = ['einordnung', 'title', 'created_at', 'changed_at']
    # actions = ['move_on', 'send_invite', 'decline']
    search_fields = ['einordnung', 'title', 'summary']


class SupporterAdmin(admin.ModelAdmin):
	list_display = ['created_at', 'initiative', 'user', 'initiator', 'first', 'ack']
	ordering = ['created_at']

	search_fields = ['initiative__title', 'user__username', 'user__first_name', 'user__last_name']


class ModerationAdmin(admin.ModelAdmin):
	list_display = ['created_at', 'initiative', 'user', 'vote', 'stale']
	ordering = ['created_at']

	search_fields = ['initiative__title', 'user__username', 'user__first_name', 'user__last_name']


admin.site.register(Initiative, InitiativeAdmin)
admin.site.register(Quorum)
admin.site.register(Supporter, SupporterAdmin)
admin.site.register(Pro)
admin.site.register(Contra)
admin.site.register(Proposal)
admin.site.register(Comment)
admin.site.register(Moderation, ModerationAdmin)
admin.site.register(Vote)
admin.site.register(Option)
admin.site.register(Preference)