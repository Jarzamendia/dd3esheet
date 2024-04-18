from django.forms import ModelForm
from django import forms
from .models import Character, CharacterStats

from crispy_forms.helper import FormHelper

from django.urls import reverse_lazy


class newCharacterForm(ModelForm):
    class Meta:
        model = Character
        fields = '__all__'
        exclude = ['Description',]

class CharacterForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'characterForm'
        
        self.helper.attrs = {
            'hx-post': reverse_lazy('character', kwargs={'pk': self.instance.id}),
            'hx-target': '#characterForm',
            'hx-push-url': 'true',
            'hx-trigger': 'change',
        }

    class Meta:
        model = Character
        fields = '__all__'
        exclude = ['Description',]
        widgets = {
            'User': forms.TextInput(attrs={'type': 'hidden'}),
        }

class CharacterStatsForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'characterStatsForm'
        
        self.helper.attrs = {
            'hx-post': reverse_lazy('character', kwargs={'pk': self.instance.id}),
            'hx-target': '#characterStatsForm',
            'hx-push-url': 'true',
            'hx-trigger': 'change',
        }

    class Meta:
        model = CharacterStats
        fields = '__all__'
        exclude = ['Character',]
        widgets = {
            'User': forms.TextInput(attrs={'type': 'hidden'}),
        }