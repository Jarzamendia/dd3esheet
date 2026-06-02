import django_filters

from .models import (
    SDR_Class,
    SDR_Domain,
    SDR_Equipment,
    SDR_Feat,
    SDR_Item,
    SDR_Monster,
    SDR_Power,
    SDR_Skill,
    SDR_Spell,
)


class BaseSdrFilterSet(django_filters.FilterSet):
    query_model = None

    def __init__(self, *args, **kwargs):
        queryset = kwargs.get("queryset")
        if queryset is None and self.query_model is not None:
            kwargs["queryset"] = self.query_model.objects.using("sdr")
        super().__init__(*args, **kwargs)

        for bound_field in self.form.visible_fields():
            bound_field.field.widget.attrs.update(
                {
                    "class": "sdr-filter-input",
                    "placeholder": bound_field.label,
                }
            )


class SpellsFilter(BaseSdrFilterSet):
    query_model = SDR_Spell

    name = django_filters.CharFilter(lookup_expr="icontains", label="Nome")
    school = django_filters.CharFilter(lookup_expr="icontains", label="Escola")
    level = django_filters.CharFilter(lookup_expr="icontains", label="Nível")
    components = django_filters.CharFilter(lookup_expr="icontains", label="Componentes")

    class Meta:
        model = SDR_Spell
        fields = ["name", "school", "level", "components"]


class MonsterFilter(BaseSdrFilterSet):
    query_model = SDR_Monster

    name = django_filters.CharFilter(lookup_expr="icontains", label="Nome")
    family = django_filters.CharFilter(lookup_expr="icontains", label="Família")
    type = django_filters.CharFilter(lookup_expr="icontains", label="Tipo")

    class Meta:
        model = SDR_Monster
        fields = ["name", "family", "type"]


class ClassFilter(BaseSdrFilterSet):
    query_model = SDR_Class

    name = django_filters.CharFilter(lookup_expr="icontains", label="Nome")
    type = django_filters.CharFilter(lookup_expr="icontains", label="Tipo")
    alignment = django_filters.CharFilter(lookup_expr="icontains", label="Alinhamento")

    class Meta:
        model = SDR_Class
        fields = ["name", "type", "alignment"]


class DomainFilter(BaseSdrFilterSet):
    query_model = SDR_Domain

    name = django_filters.CharFilter(lookup_expr="icontains", label="Nome")

    class Meta:
        model = SDR_Domain
        fields = ["name"]


class EquipmentFilter(BaseSdrFilterSet):
    query_model = SDR_Equipment

    name = django_filters.CharFilter(lookup_expr="icontains", label="Nome")
    family = django_filters.CharFilter(lookup_expr="icontains", label="Família")
    category = django_filters.CharFilter(lookup_expr="icontains", label="Categoria")
    type = django_filters.CharFilter(lookup_expr="icontains", label="Tipo")

    class Meta:
        model = SDR_Equipment
        fields = ["name", "family", "category", "type"]


class FeatFilter(BaseSdrFilterSet):
    query_model = SDR_Feat

    name = django_filters.CharFilter(lookup_expr="icontains", label="Nome")
    type = django_filters.CharFilter(lookup_expr="icontains", label="Tipo")
    prerequisite = django_filters.CharFilter(lookup_expr="icontains", label="Pré-requisito")

    class Meta:
        model = SDR_Feat
        fields = ["name", "type", "prerequisite"]


class ItemFilter(BaseSdrFilterSet):
    query_model = SDR_Item

    name = django_filters.CharFilter(lookup_expr="icontains", label="Nome")
    category = django_filters.CharFilter(lookup_expr="icontains", label="Categoria")
    subcategory = django_filters.CharFilter(lookup_expr="icontains", label="Subcategoria")

    class Meta:
        model = SDR_Item
        fields = ["name", "category", "subcategory"]


class PowerFilter(BaseSdrFilterSet):
    query_model = SDR_Power

    name = django_filters.CharFilter(lookup_expr="icontains", label="Nome")
    discipline = django_filters.CharFilter(lookup_expr="icontains", label="Disciplina")
    level = django_filters.CharFilter(lookup_expr="icontains", label="Nível")

    class Meta:
        model = SDR_Power
        fields = ["name", "discipline", "level"]


class SkillFilter(BaseSdrFilterSet):
    query_model = SDR_Skill

    name = django_filters.CharFilter(lookup_expr="icontains", label="Nome")
    key_ability = django_filters.CharFilter(lookup_expr="icontains", label="Habilidade-chave")

    class Meta:
        model = SDR_Skill
        fields = ["name", "key_ability"]
