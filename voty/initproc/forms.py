from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model

from dal import autocomplete
from uuid import uuid4

from .models import Pro, Contra, Like, Comment, Proposal, Moderation, Initiative


def simple_form_verifier(form_cls, template="fragments/simple_form.html", via_ajax=True,
                         submit_klasses="btn-outline-primary", submit_title="Abschicken"):
    def wrap(fn):
        def view(request, *args, **kwargs):
            if request.method == "POST":
                form = form_cls(request.POST)
                if form.is_valid():
                    return fn(request, form, *args, **kwargs)
            else:
                form = form_cls(initial=request.GET)

            fragment = request.GET.get('fragment')
            rendered = render_to_string(template,
                        context=dict(fragment=fragment, form=form, ajax=via_ajax,
                                     submit_klasses=submit_klasses,
                                     submit_title=submit_title),
                        request=request)
            if fragment:
                return {'inner-fragments': {fragment: rendered}}
            return rendered
        return view
    return wrap


class SubmitButton(forms.Widget):
    """
    A widget that handles a submit button.
    """
    def __init__(self, name, value, label, attrs):
        self.name, self.value, self.label = name, value, label
        self.attrs = attrs
        
    def render(self):
        label = self.label
        icon = self.attrs.pop('icon', None)
        if icon:
            label = '<i class="material-icons">{}</i>'.format(icon)

        final_attrs = self.build_attrs(
            self.attrs,
            type="submit",
            name="{}-btn".format(self.name),
            value=self.value,
            )

        return mark_safe(u'<button {}>{}</button>'.format(
            forms.widgets.flatatt(final_attrs),
            label,
            ))

class MultipleSubmitButton(forms.Select):
    """
    A widget that handles a list of submit buttons.
    """
    def __init__(self, attrs={}, btn_attrs={}, choices=()):
        self.attrs = attrs
        self.choices = choices
        self.btn_attrs = btn_attrs
        self.uid  = uuid4().hex

    def buttons(self):
        for value, label in self.choices:
            attrs = self.attrs.copy()
            if value in self.btn_attrs:
                attrs.update(self.btn_attrs[value])
            # attrs['class'] = attrs.get('class','') + " {}-submit-btn".format(self.uid)
            yield SubmitButton(self.name, value, label, attrs)

        
    def render(self, name, value, attrs=None, choices=()):
        self.name = name
        return mark_safe('\n'.join([w.render() for w in self.buttons()]))

    def value_from_datadict(self, data, files, name):
        """
        returns the value of the widget: IE posts inner HTML of the button
        instead of the value.
        """
        value = data.get(name, None)
        if value in dict(self.choices):
            print("found")
            return value
        else:
            inside_out_choices = dict([(v, k) for (k, v) in self.choices])
            if value in inside_out_choices:
                return inside_out_choices[value]
        return None

class InviteUsersForm(forms.Form):
    user = forms.ModelMultipleChoiceField(
        label="Einladen",
        queryset=get_user_model().objects,
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
                    url='user_autocomplete',
                    attrs={"data-placeholder": "Zum Suchen tippen",
                           'data-html': "True"}))


class InitiativeForm(forms.ModelForm):

    class Meta:
        model = Initiative
        fields = ['title', 'subtitle', 'summary', 'problem', 'forderung',
                  'kosten', 'fin_vorschlag', 'arbeitsweise', 'init_argument',
                  'einordnung', 'ebene', 'bereich']

        labels = {
            "title" : "Überschrift",
            "subtitle": "Anreißer",
            "summary" : "Zusammenfassung",
            "problem": "Problembeschreibung",
            "forderung" : "Forderung",
            "kosten": "Kosten",
            "fin_vorschlag": "Finanzierungsvorschlag",
            "arbeitsweise": "Arbeitsweise",
            "init_argument": "Argument der Initiator/innen",
        }
        help_texts = {
            "title" : "Die Überschrift sollte kurz und knackig Eure Forderung enthalten.",
            "subtitle": "Hier reißt Ihr kurz das Problem an, welches Eure Initiative lösen soll. Versucht es auf 1-2 Sätze zu beschränken.",
            "summary" : "Hier schreibt bitte 3-4 Sätze, die zusammenfassen, worum es in dieser Initiative geht.",
            "problem": "Hier bitte in 3-4 Sätzen das Problem beschreiben, das Ihr mit Eurer Initiative lösen wollt.",
            "forderung" : "Was sind Eure konkreten Forderungen?",
            "kosten": "Entstehen Kosten für Eure Initiative? Versucht bitte, wenn möglich, eine ungefähre Einschätzung über die Höhe der Kosten zu geben.",
            "fin_vorschlag": "Hier solltet Ihr kurz erklären, wie die Kosten gedeckt werden könnten. Hier reicht auch zu schreiben, dass die Initiative über Steuereinnahmen finanziert wird.",
            "arbeitsweise": "Habt Ihr mit Expert/innen gesprochen? Wo kommen Eure Informationen her? Hier könnt Ihr auch Quellen angeben.",
            "init_argument": "Hier dürft Ihr emotional werden: Warum ist Euch das wichtig und warum bringt Ihr diese Initiative ein?",

        }


class NewArgumentForm(forms.Form):
    TITLE = "Neues Argument hinzufügen"
    type = forms.ChoiceField(choices=[('👍', '👍'), ('👎', '👎')], widget=forms.HiddenInput())
    title = forms.CharField(required=True,
                            label="Zusammenfassung",
                            max_length=140,
                            widget=forms.Textarea(attrs={'rows':3, 'placeholder':'Wir wollen die Argumente so übersichtlich wie möglich halten. Bitte achte darauf, dass Dein Argument wirklich neu ist.'}))
    text = forms.CharField(required=True,
                           label="Ausführliche Darstellung",
                           max_length=500,
                           widget=forms.Textarea(attrs={'rows':10, 'placeholder':'Wenn es bereits ein ähnliches Argument gibt, dann äußere Dich bitte in den Kommentaren zu diesem.'}))


class NewProposalForm(forms.Form):
    title = forms.CharField(required=True,
                            label="Zusammenfassung",
                            max_length=140,
                            widget=forms.Textarea(attrs={'rows':3, 'placeholder':'Wir wollen die Vorschläge so übersichtlich wie möglich halten. Bitte achte darauf, dass Dein Vorschlag wirklich neu ist.'}))
    text = forms.CharField(required=True,
                           label="Ausführliche Darstellung",
                           max_length=1000,
                           widget=forms.Textarea(attrs={'rows':10, 'placeholder':'Wenn es bereits einen ähnlichen Vorschlag gibt, dann äußere Dich bitte in den Kommentaren zu diesem.'}))


class NewCommentForm(forms.ModelForm):
    text = forms.CharField(required=True, label="Dein Kommentar",
                           help_text="Absätze sowie URLs werden passend formatiert",
                           max_length=500, widget=forms.Textarea(attrs={'rows':10, 'placeholder':'Bitte beziehe Dich in Deinem Kommentar auf das obige Argument.'}))

    class Meta:
        model = Comment
        fields = ['text']


QUESTIONS_COUNT = 11
class NewModerationForm(forms.ModelForm):


    TITLE = "Moderation"
    TEXT = "Die Inititiative ... (bitte nicht passendes streichen)"

    q0 = forms.BooleanField(required=False, initial=True, label="Widerspricht in irgendeinem Punkt den Menschenrechten oder der Würde des Menschen")
    q1 = forms.BooleanField(required=False, initial=True, label="Enthält abwertende Begriffe gegen Gruppen (zB “Asylanten”)")
    q2 = forms.BooleanField(required=False, initial=True, label="Ist ausgrenzend/rassistisch/homophob/behindertenfeindlich/transphob/sexistisch")
    q3 = forms.BooleanField(required=False, initial=True, label="Ist nationalistisch")
    q4 = forms.BooleanField(required=False, initial=True, label="Ist un-demokratisch?")
    q5 = forms.BooleanField(required=False, initial=True, label="Führt zu weniger Transparenz")
    q6 = forms.BooleanField(required=False, initial=True, label="Führt zu weiterer Bevormundung oder Ausschluss von Personen an der Beteiligung")
    q7 = forms.BooleanField(required=False, initial=True, label="Läuft auf Kosten folgender Generationen")
    q8 = forms.BooleanField(required=False, initial=True, label="Gefährdet unser Klima und unseren Planeten")
    q9 = forms.BooleanField(required=False, initial=True, label="Trägt dazu bei, dass Reiche noch reicher werden und/oder Arme noch ärmer")
    q10 = forms.BooleanField(required=False, initial=True, label="Benachteiligt bestimmte Personengruppen, die sowieso schon benachteiligt sind")
    # this box is not like the others
    constitution_change = forms.BooleanField(required=False, initial=False, label="Erfordert eine Änderung des Grundgesetzes")
    text = forms.CharField(required=False, label="Kommentar/Hinweis/Anmerkung", widget=forms.Textarea)
    vote = forms.ChoiceField(required=True, label="Deine Beurteilung",
            choices=[('y', 'yay'),('n', 'nope')],
            widget=forms.RadioSelect())
            # widget=MultipleSubmitButton(btn_attrs={
            #     'y': { 'class': 'btn btn-outline-success',
            #            'icon': 'thumb_up' },
            #     'n': {'class': 'btn btn-outline-danger',
            #            'icon': 'thumb_down'}
            #     }))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['vote'] == 'y':
            for i in range(QUESTIONS_COUNT):
                if cleaned_data['q{}'.format(i) ]:
                    self.add_error("vote", "Du darfst nicht positiv werten, wenn Du mindestens ein Problem oben markiert hast.")
                    break
            if cleaned_data['constitution_change'] and not cleaned_data['text']:
                self.add_error("vote", "Bitte gib einen Kommentar dazu ab, dass die Initiative eine Grundgesetzänderung erfordert.")
        else:
            if not cleaned_data['text']:
                self.add_error("text", "Kannst Du das bitte begründen?")

    class Meta:
        model = Moderation
        fields = ['q{}'.format(i) for i in range(QUESTIONS_COUNT)] + ['constitution_change', 'text', 'vote']

