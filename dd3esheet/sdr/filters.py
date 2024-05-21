import django_filters

from .models import *


class SpellsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    school = django_filters.CharFilter(lookup_expr='icontains')
    level = django_filters.CharFilter(lookup_expr='icontains')
    components = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Spell
        fields = [
            "name",
            "school",
            "level",
            "components"
        ] 

class MonsterFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    family = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = SDR_Monster
        fields = [
            "name",
            "family",
            "type",
        ] 
