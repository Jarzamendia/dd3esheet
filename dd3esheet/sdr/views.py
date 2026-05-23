from django.shortcuts import render, get_object_or_404
from .models import (
    SDR_Class, SDR_ClassTable, SDR_Domain, SDR_Equipment, SDR_Feat,
    SDR_Item, SDR_Monster, SDR_Power, SDR_Skill, SDR_Spell,
)
from .filters import (
    SpellsFilter, MonsterFilter, ClassFilter, DomainFilter,
    EquipmentFilter, FeatFilter, ItemFilter, PowerFilter, SkillFilter,
)


def home(request):
    return render(request, 'sdr/home.html')


# --- Spells ---

def spells(request):
    filtered = SpellsFilter(
        request.GET,
        queryset=SDR_Spell.objects.using('sdr').order_by('name'),
    )
    return render(request, 'sdr/spells.html', {'filtered_spells': filtered})


def spell(request, pk):
    obj = SDR_Spell.objects.using('sdr').get(id=pk)
    return render(request, 'sdr/spell.html', {'spell': obj})


# --- Monsters ---

def monsters(request):
    filtered = MonsterFilter(
        request.GET,
        queryset=SDR_Monster.objects.using('sdr').order_by('name'),
    )
    return render(request, 'sdr/monsters.html', {'filtered_monsters': filtered})


def monster(request, pk):
    obj = SDR_Monster.objects.using('sdr').get(id=pk)
    return render(request, 'sdr/monster.html', {'monster': obj})


# --- Classes ---

def classes(request):
    filtered = ClassFilter(
        request.GET,
        queryset=SDR_Class.objects.using('sdr').order_by('name'),
    )
    return render(request, 'sdr/classes.html', {'filtered_classes': filtered})


def dnd_class(request, pk):
    obj = SDR_Class.objects.using('sdr').get(id=pk)
    table = SDR_ClassTable.objects.using('sdr').filter(name=obj.name).order_by('level')
    return render(request, 'sdr/class.html', {'dnd_class': obj, 'class_table': table})


# --- Domains ---

def domains(request):
    filtered = DomainFilter(
        request.GET,
        queryset=SDR_Domain.objects.using('sdr').order_by('name'),
    )
    return render(request, 'sdr/domains.html', {'filtered_domains': filtered})


def domain(request, pk):
    obj = SDR_Domain.objects.using('sdr').get(id=pk)
    return render(request, 'sdr/domain.html', {'domain': obj})


# --- Equipment ---

def equipment_list(request):
    filtered = EquipmentFilter(
        request.GET,
        queryset=SDR_Equipment.objects.using('sdr').order_by('name'),
    )
    return render(request, 'sdr/equipment_list.html', {'filtered_equipment': filtered})


def equipment(request, pk):
    obj = SDR_Equipment.objects.using('sdr').get(id=pk)
    return render(request, 'sdr/equipment.html', {'equipment': obj})


# --- Feats ---

def feats(request):
    filtered = FeatFilter(
        request.GET,
        queryset=SDR_Feat.objects.using('sdr').order_by('name'),
    )
    return render(request, 'sdr/feats.html', {'filtered_feats': filtered})


def feat(request, pk):
    obj = SDR_Feat.objects.using('sdr').get(id=pk)
    return render(request, 'sdr/feat.html', {'feat': obj})


# --- Items ---

def items(request):
    filtered = ItemFilter(
        request.GET,
        queryset=SDR_Item.objects.using('sdr').order_by('name'),
    )
    return render(request, 'sdr/items.html', {'filtered_items': filtered})


def item(request, pk):
    obj = SDR_Item.objects.using('sdr').get(id=pk)
    return render(request, 'sdr/item.html', {'item': obj})


# --- Powers ---

def powers(request):
    filtered = PowerFilter(
        request.GET,
        queryset=SDR_Power.objects.using('sdr').order_by('name'),
    )
    return render(request, 'sdr/powers.html', {'filtered_powers': filtered})


def power(request, pk):
    obj = SDR_Power.objects.using('sdr').get(id=pk)
    return render(request, 'sdr/power.html', {'power': obj})


# --- Skills ---

def skills(request):
    filtered = SkillFilter(
        request.GET,
        queryset=SDR_Skill.objects.using('sdr').order_by('name'),
    )
    return render(request, 'sdr/skills.html', {'filtered_skills': filtered})


def skill(request, pk):
    obj = SDR_Skill.objects.using('sdr').get(id=pk)
    return render(request, 'sdr/skill.html', {'skill': obj})
