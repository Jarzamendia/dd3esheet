from django.forms import ModelForm
from django import forms
from .models import Character, CharacterStats

from crispy_forms.helper import FormHelper
from django.urls import reverse_lazy

from .constants import ALIGNMENT_CHOICES, SIZE_CHOICES, RACE_CHOICES


class CharacterCreateForm(ModelForm):
    class Meta:
        model = Character
        fields = ['Name', 'Description']
        widgets = {
            'Name': forms.TextInput(attrs={
                'class': 'paper-input',
                'placeholder': 'Nome do personagem',
            }),
            'Description': forms.Textarea(attrs={
                'class': 'paper-input',
                'rows': 4,
                'placeholder': 'Uma frase ou parágrafo sobre quem é (opcional).',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Name'].required = True
        self.helper = FormHelper()
        self.helper.form_id = 'characterCreateForm'
        self.helper.form_tag = False


class CharacterIdentityForm(ModelForm):
    class Meta:
        model = Character
        fields = [
            'Name', 'Class', 'Level', 'Race', 'Alignment', 'Deity',
            'Size', 'Age', 'Sex', 'Heigth', 'Weight', 'Eye', 'Hair', 'Skin',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Name'].required = True
        self.helper = FormHelper()
        self.helper.form_id = 'characterIdentityForm'
        self.helper.form_tag = False
        pk = self.instance.pk if self.instance and self.instance.pk else 0
        self.helper.attrs = {
            'hx-post': reverse_lazy('character:character', kwargs={'pk': pk}),
            'hx-target': '#characterIdentityForm',
            'hx-swap': 'outerHTML',
            'hx-trigger': 'change delay:300ms',
        }
        # Lazy import to avoid circular — services imports constants which imports nothing
        from .services import sdr_class_choices
        self.fields['Class'] = forms.ChoiceField(
            choices=sdr_class_choices(),
            required=False,
            widget=forms.Select(attrs={'class': 'field-slot'}),
        )
        self.fields['Alignment'] = forms.ChoiceField(
            choices=ALIGNMENT_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'field-slot'}),
        )
        self.fields['Size'] = forms.ChoiceField(
            choices=SIZE_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'field-slot'}),
        )
        self.fields['Race'] = forms.ChoiceField(
            choices=RACE_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'field-slot'}),
        )


class CharacterForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'characterForm'
        self.helper.attrs = {
            'hx-post': reverse_lazy('character:character', kwargs={'pk': self.instance.id}),
            'hx-target': '#characterForm',
            'hx-push-url': 'true',
            'hx-trigger': 'change',
        }

    class Meta:
        model = Character
        fields = ['Description']


class CharacterStatsForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'characterStatsForm'
        pk = self.instance.Character_id if self.instance and self.instance.pk else 0
        self.helper.attrs = {
            'hx-post': reverse_lazy('character:character', kwargs={'pk': pk}),
            'hx-target': '#characterStatsForm',
            'hx-push-url': 'true',
            'hx-trigger': 'change',
        }

    class Meta:
        model = CharacterStats
        fields = '__all__'
        exclude = ['Character']
