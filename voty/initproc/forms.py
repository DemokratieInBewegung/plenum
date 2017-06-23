from django import forms
from .models import Pro, Contra, Like, Proposal


class NewArgumentForm(forms.Form):
	type = forms.ChoiceField(choices=[('👍', '👍'), ('👎', '👎')], widget=forms.RadioSelect())
	title = forms.CharField(required=True, max_length=80)
	text = forms.CharField(required=True, max_length=500)
