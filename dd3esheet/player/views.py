from django.shortcuts import render
from django.http import HttpResponse
from django.forms import ModelForm
from .models import PlayerDescription


# Create the form class.
class PlayerDescriptionForm(ModelForm):
    class Meta:
        model = PlayerDescription
        fields = '__all__'

# Create your views here.
def index(request):
    
    # Creating a form to add an article.
    form = PlayerDescriptionForm(prefix='form1')
    return HttpResponse(form)
