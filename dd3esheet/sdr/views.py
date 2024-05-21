from django.shortcuts import render
from .models import *
from .filters import *

# Create your views here.
def home(request):
    return render(request, 'sdr/home.html')

def spells(request):

    filtered_spells = SpellsFilter(
        request.GET,
        queryset=SDR_Spell.objects.using('sdr').order_by('name')
    )

    return render(request, 'sdr/spells.html', {'filtered_spells': filtered_spells})


def spell(request, pk):
    spell = SDR_Spell.objects.using('sdr').get(id=pk)

    context = {
        "spell": spell
    }

    return render(request, "sdr/spell.html", context)


def monsters(request):

    filtered_monsters = MonsterFilter(
        request.GET,
        queryset=SDR_Monster.objects.using('sdr').order_by('name')
    )

    return render(request, 'sdr/monsters.html', {'filtered_monsters': filtered_monsters})

def monster(request, pk):
    monster = SDR_Monster.objects.using('sdr').get(id=pk)

    context = {
        "monster": monster
    }

    return render(request, "sdr/monster.html", context)
