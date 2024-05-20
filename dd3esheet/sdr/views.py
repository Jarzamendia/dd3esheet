from django.shortcuts import render
from .models import *

# Create your views here.
def home(request):
    return render(request, 'sdr/home.html')

def spells(request):

    spells = SDR_Spell.objects.using('sdr').order_by('name')
    
    return render(request, 'sdr/spells.html', {'spells': spells})

def spell(request, pk):
    spell = SDR_Spell.objects.using('sdr').get(id=pk)

    context = {
        "spell": spell
    }

    return render(request, "sdr/spell.html", context)