from django import forms
from .models import Pro, Contra, Like, Comment, Proposal


class NewArgumentForm(forms.Form):
    type = forms.ChoiceField(choices=[('👍', '👍'), ('👎', '👎')], widget=forms.RadioSelect())
    title = forms.CharField(required=True, max_length=80)
    text = forms.CharField(required=True, max_length=500, widget=forms.Textarea())


class NewProposalForm(forms.Form):
    text = forms.CharField(required=True, max_length=1024, widget=forms.Textarea())


class NewCommentForm(forms.ModelForm):
    
    class Meta:
        model = Comment
        fields = ['text']

