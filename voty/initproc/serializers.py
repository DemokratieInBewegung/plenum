from rest_framework import serializers
from .models import Initiative

class SimpleInitiativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Initiative
        fields = ["id", "title", "subtitle", "state", "created_at",
                  "changed_at","summary", "problem", "forderung",
                  "kosten", "fin_vorschlag", "arbeitsweise", "init_argument" ,
                  "einordnung", "ebene", "bereich", "went_public_at",
                  "went_to_discussion_at", "went_to_voting_at", "was_closed_at",
                  # and calculated fields also matter:
                  "slug", "end_of_this_phase",
                  "type"]


