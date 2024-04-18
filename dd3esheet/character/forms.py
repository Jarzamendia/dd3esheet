from django.forms import ModelForm
from django import forms
from .models import Character, CharacterStats

class CharacterForm(ModelForm):

    class Meta:
        model = Character
        fields = '__all__'
        exclude = ['Description',]
        widgets = {
            'User': forms.TextInput(attrs={'type': 'hidden'}),
        }

class CharacterStatsForm(ModelForm):
    class Meta:
        model = CharacterStats
        fields = '__all__'
        exclude = ['Character',]
        widgets = {
            'User': forms.TextInput(attrs={'type': 'hidden'}),
        }