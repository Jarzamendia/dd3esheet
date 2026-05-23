import django_filters

from .models import (
    SDR_Class, SDR_Domain, SDR_Equipment, SDR_Feat,
    SDR_Item, SDR_Monster, SDR_Power, SDR_Skill, SDR_Spell,
)


class SpellsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    school = django_filters.CharFilter(lookup_expr='icontains')
    level = django_filters.CharFilter(lookup_expr='icontains')
    components = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Spell
        fields = ["name", "school", "level", "components"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', SDR_Spell.objects.using('sdr'))
        super().__init__(*args, **kwargs)


class MonsterFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    family = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Monster
        fields = ["name", "family", "type"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', SDR_Monster.objects.using('sdr'))
        super().__init__(*args, **kwargs)


class ClassFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.CharFilter(lookup_expr='icontains')
    alignment = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Class
        fields = ["name", "type", "alignment"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', SDR_Class.objects.using('sdr'))
        super().__init__(*args, **kwargs)


class DomainFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Domain
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', SDR_Domain.objects.using('sdr'))
        super().__init__(*args, **kwargs)


class EquipmentFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    family = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Equipment
        fields = ["name", "family", "category", "type"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', SDR_Equipment.objects.using('sdr'))
        super().__init__(*args, **kwargs)


class FeatFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.CharFilter(lookup_expr='icontains')
    prerequisite = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Feat
        fields = ["name", "type", "prerequisite"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', SDR_Feat.objects.using('sdr'))
        super().__init__(*args, **kwargs)


class ItemFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.CharFilter(lookup_expr='icontains')
    subcategory = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Item
        fields = ["name", "category", "subcategory"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', SDR_Item.objects.using('sdr'))
        super().__init__(*args, **kwargs)


class PowerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    discipline = django_filters.CharFilter(lookup_expr='icontains')
    level = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Power
        fields = ["name", "discipline", "level"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', SDR_Power.objects.using('sdr'))
        super().__init__(*args, **kwargs)


class SkillFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    key_ability = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Skill
        fields = ["name", "key_ability"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', SDR_Skill.objects.using('sdr'))
        super().__init__(*args, **kwargs)
