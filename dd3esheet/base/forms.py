from django.forms import ModelForm
from .models import Character, CharacterDescription

class CharacterForm(ModelForm):
    class Meta:
        model = Character
        fields = '__all__'

class CharacterDescription(ModelForm):
    class Meta:
        model = CharacterDescription
        fields = '__all__'

        