from django.forms import ModelForm
from .models import Character, CharacterStats

class CharacterForm(ModelForm):
    class Meta:
        model = Character
        fields = '__all__'


class CharacterStatsForm(ModelForm):
    class Meta:
        model = CharacterStats
        fields = '__all__'
        exclude = ['Character',]
