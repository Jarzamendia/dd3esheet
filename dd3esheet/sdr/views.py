from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .filters import (
    ClassFilter,
    DomainFilter,
    EquipmentFilter,
    FeatFilter,
    ItemFilter,
    MonsterFilter,
    PowerFilter,
    SkillFilter,
    SpellsFilter,
)
from .models import (
    SDR_Class,
    SDR_ClassTable,
    SDR_Domain,
    SDR_Equipment,
    SDR_Feat,
    SDR_Item,
    SDR_Monster,
    SDR_Power,
    SDR_Skill,
    SDR_Spell,
)


HOME_CATEGORIES = [
    {
        "badge": "MAG",
        "title": "Magias",
        "description": "Escolas, componentes, alcance e descrições das magias do SRD.",
        "url_name": "sdr:spells",
    },
    {
        "badge": "MON",
        "title": "Monstros",
        "description": "Blocos de estatísticas, ataques e informações de encontro.",
        "url_name": "sdr:monsters",
    },
    {
        "badge": "CLA",
        "title": "Classes",
        "description": "Características de classe, progressão e tabelas por nível.",
        "url_name": "sdr:classes",
    },
    {
        "badge": "DOM",
        "title": "Domínios",
        "description": "Poderes concedidos e magias de domínio organizadas por círculo.",
        "url_name": "sdr:domains",
    },
    {
        "badge": "EQU",
        "title": "Equipamentos",
        "description": "Armas, armaduras e outros itens mundanos com custo e peso.",
        "url_name": "sdr:equipment",
    },
    {
        "badge": "TAL",
        "title": "Talentos",
        "description": "Pré-requisitos, benefícios e regras especiais dos talentos.",
        "url_name": "sdr:feats",
    },
    {
        "badge": "ITM",
        "title": "Itens Mágicos",
        "description": "Auras, pré-requisitos, preços e efeitos de itens encantados.",
        "url_name": "sdr:items",
    },
    {
        "badge": "PSI",
        "title": "Poderes Psiônicos",
        "description": "Disciplinas, custo em pontos de poder e opções de augment.",
        "url_name": "sdr:powers",
    },
    {
        "badge": "SKL",
        "title": "Perícias",
        "description": "Habilidades-chave, uso sem treino e aplicações detalhadas.",
        "url_name": "sdr:skills",
    },
]


def _has_value(value):
    return value not in (None, "")


def _join_bits(*values):
    parts = [str(value).strip() for value in values if _has_value(value) and str(value).strip()]
    return " • ".join(parts)


def _row(label, value):
    if not _has_value(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return {"label": label, "value": text}


def _rows(*pairs):
    return [row for row in (_row(label, value) for label, value in pairs) if row]


def _text_block(title, content):
    if not _has_value(content):
        return None
    text = str(content).strip()
    if not text:
        return None
    return {"title": title, "content": text}


def _text_blocks(*pairs):
    return [block for block in (_text_block(title, content) for title, content in pairs) if block]


def _breadcrumbs(*items):
    crumbs = []
    for label, url_name, args in items:
        crumb = {"label": label}
        if url_name:
            crumb["url"] = reverse(url_name, args=args or [])
        crumbs.append(crumb)
    return crumbs


def _page_context(page_title, breadcrumbs, **extra):
    context = {
        "page_title": page_title,
        "breadcrumbs": breadcrumbs,
        "sdr_sheet_wide": True,
    }
    context.update(extra)
    return context


def _list_context(page_title, page_description, filterset):
    return _page_context(
        page_title=page_title,
        page_description=page_description,
        breadcrumbs=_breadcrumbs(
            ("Referência", "sdr:home", None),
            (page_title, None, None),
        ),
        filterset=filterset,
        results_count=filterset.qs.count(),
    )


def _detail_context(page_title, category_title, category_url_name, object_name, **extra):
    return _page_context(
        page_title=page_title,
        breadcrumbs=_breadcrumbs(
            ("Referência", "sdr:home", None),
            (category_title, category_url_name, None),
            (object_name, None, None),
        ),
        back_url=reverse(category_url_name),
        back_label=f"Voltar para {category_title}",
        **extra,
    )


def _full_text_fallback(instance, *content_groups):
    has_structured_content = any(group for group in content_groups)
    return instance.full_text if not has_structured_content and _has_value(instance.full_text) else None


def home(request):
    categories = [
        {
            **category,
            "url": reverse(category["url_name"]),
        }
        for category in HOME_CATEGORIES
    ]
    context = _page_context(
        page_title="Referência — D&D 3.5",
        breadcrumbs=[{"label": "Referência"}],
        page_description="Navegue pelo SRD de D&D 3.5 com filtros rápidos e fichas legíveis.",
        categories=categories,
    )
    return render(request, "sdr/home.html", context)


def spells(request):
    filtered = SpellsFilter(
        request.GET,
        queryset=SDR_Spell.objects.using("sdr").order_by("name"),
    )
    context = _list_context(
        page_title="Magias",
        page_description="Escolas, componentes e descrições organizadas como consulta rápida.",
        filterset=filtered,
    )
    context["filtered_spells"] = filtered
    return render(request, "sdr/spells.html", context)


def spell(request, pk):
    obj = get_object_or_404(SDR_Spell.objects.using("sdr"), id=pk)
    primary_rows = _rows(
        ("Escola", obj.school),
        ("Subescola", obj.subschool),
        ("Descritor", obj.descriptor),
        ("Nível", obj.level),
        ("Componentes", obj.components),
        ("Tempo de Conjuração", obj.casting_time),
        ("Alcance", obj.range),
        ("Alvo", obj.target),
        ("Área", obj.area),
        ("Efeito", obj.effect),
        ("Duração", obj.duration),
        ("Teste de Resistência", obj.saving_throw),
        ("Resistência à Magia", obj.spell_resistance),
    )
    text_sections = _text_blocks(
        ("Resumo", obj.short_description),
        ("Descrição", obj.description),
        ("Componentes Materiais", obj.material_components),
        ("Foco", obj.focus),
        ("Custo em XP", obj.xp_cost),
    )
    context = _detail_context(
        page_title="Magias",
        category_title="Magias",
        category_url_name="sdr:spells",
        object_name=obj.name,
        detail_title=obj.name,
        detail_subtitle=_join_bits(obj.altname, obj.school, obj.level),
        summary_rows=primary_rows,
        text_sections=text_sections,
        fallback_full_text=_full_text_fallback(obj, primary_rows, text_sections),
    )
    return render(request, "sdr/spell.html", context)


def monsters(request):
    filtered = MonsterFilter(
        request.GET,
        queryset=SDR_Monster.objects.using("sdr").order_by("name"),
    )
    context = _list_context(
        page_title="Monstros",
        page_description="Blocos de estatísticas, ambiente, organização e desafios.",
        filterset=filtered,
    )
    context["filtered_monsters"] = filtered
    return render(request, "sdr/monsters.html", context)


def monster(request, pk):
    obj = get_object_or_404(SDR_Monster.objects.using("sdr"), id=pk)
    primary_rows = _rows(
        ("Família", obj.family),
        ("Tamanho", obj.size),
        ("Tipo", obj.type),
        ("Dados de Vida", obj.hit_dice),
        ("Iniciativa", obj.initiative),
        ("Deslocamento", obj.speed),
        ("Classe de Armadura", obj.armor_class),
        ("BBA", obj.base_attack),
        ("Agarrar", obj.grapple),
        ("Ataque", obj.attack),
        ("Ataque Completo", obj.full_attack),
        ("Espaço", obj.space),
        ("Alcance", obj.reach),
        ("Testes de Resistência", obj.saves),
        ("Atributos", obj.abilities),
        ("Ambiente", obj.environment),
        ("Organização", obj.organization),
        ("Nível de Desafio", obj.challenge_rating),
        ("Tesouro", obj.treasure),
        ("Alinhamento", obj.alignment),
        ("Progressão", obj.advancement),
        ("Ajuste de Nível", obj.level_adjustment),
    )
    text_sections = _text_blocks(
        ("Ataques Especiais", obj.special_attacks),
        ("Qualidades Especiais", obj.special_qualities),
        ("Perícias", obj.skills),
        ("Talentos", obj.feats),
        ("Habilidades Especiais", obj.special_abilities),
        ("Bloco de Estatísticas", obj.stat_block),
    )
    context = _detail_context(
        page_title="Monstros",
        category_title="Monstros",
        category_url_name="sdr:monsters",
        object_name=obj.name,
        detail_title=obj.name,
        detail_subtitle=_join_bits(obj.family, obj.size, obj.type),
        summary_rows=primary_rows,
        text_sections=text_sections,
        fallback_full_text=_full_text_fallback(obj, primary_rows, text_sections),
    )
    return render(request, "sdr/monster.html", context)


def classes(request):
    filtered = ClassFilter(
        request.GET,
        queryset=SDR_Class.objects.using("sdr").order_by("name"),
    )
    context = _list_context(
        page_title="Classes",
        page_description="Características essenciais e tabelas de progressão por nível.",
        filterset=filtered,
    )
    context["filtered_classes"] = filtered
    return render(request, "sdr/classes.html", context)


def _class_progression(table_rows):
    slot_levels = [
        level
        for level in range(10)
        if any(_has_value(getattr(row, f"slots_{level}")) for row in table_rows)
    ]
    rows = []
    for row in table_rows:
        rows.append(
            {
                "level": row.level,
                "base_attack_bonus": row.base_attack_bonus,
                "fort_save": row.fort_save,
                "ref_save": row.ref_save,
                "will_save": row.will_save,
                "special": row.special,
                "slots": [getattr(row, f"slots_{level}") for level in slot_levels],
            }
        )
    return slot_levels, rows


def dnd_class(request, pk):
    obj = get_object_or_404(SDR_Class.objects.using("sdr"), id=pk)
    class_table = list(
        SDR_ClassTable.objects.using("sdr").filter(name=obj.name).order_by("level")
    )
    slot_levels, progression_rows = _class_progression(class_table)
    primary_rows = _rows(
        ("Tipo", obj.type),
        ("Alinhamento", obj.alignment),
        ("Dado de Vida", obj.hit_die),
        ("Pontos de Perícia", obj.skill_points),
        ("Atributo de Perícia", obj.skill_points_ability),
        ("Atributo de Magia", obj.spell_stat),
        ("Tipo de Magia", obj.spell_type),
    )
    text_sections = _text_blocks(
        ("Perícias da Classe", obj.class_skills),
        ("Proficiências", obj.proficiencies),
        ("Lista Épica", obj.epic_feat_list),
    )
    context = _detail_context(
        page_title="Classes",
        category_title="Classes",
        category_url_name="sdr:classes",
        object_name=obj.name,
        detail_title=obj.name,
        detail_subtitle=_join_bits(obj.type, obj.alignment, obj.spell_type),
        summary_rows=primary_rows,
        text_sections=text_sections,
        progression_slot_levels=slot_levels,
        progression_rows=progression_rows,
        fallback_full_text=_full_text_fallback(obj, primary_rows, text_sections, progression_rows),
    )
    return render(request, "sdr/class.html", context)


def domains(request):
    filtered = DomainFilter(
        request.GET,
        queryset=SDR_Domain.objects.using("sdr").order_by("name"),
    )
    context = _list_context(
        page_title="Domínios",
        page_description="Poderes concedidos e magias agrupadas por círculo.",
        filterset=filtered,
    )
    context["filtered_domains"] = filtered
    return render(request, "sdr/domains.html", context)


def _domain_spell_rows(domain):
    return _rows(
        *[(f"{level}º círculo", getattr(domain, f"spell_{level}")) for level in range(1, 10)]
    )


def domain(request, pk):
    obj = get_object_or_404(SDR_Domain.objects.using("sdr"), id=pk)
    spell_rows = _domain_spell_rows(obj)
    text_sections = _text_blocks(("Poderes Concedidos", obj.granted_powers))
    context = _detail_context(
        page_title="Domínios",
        category_title="Domínios",
        category_url_name="sdr:domains",
        object_name=obj.name,
        detail_title=obj.name,
        detail_subtitle="Domínio divino",
        summary_rows=[],
        text_sections=text_sections,
        domain_spells=spell_rows,
        fallback_full_text=_full_text_fallback(obj, text_sections, spell_rows),
    )
    return render(request, "sdr/domain.html", context)


def equipment_list(request):
    filtered = EquipmentFilter(
        request.GET,
        queryset=SDR_Equipment.objects.using("sdr").order_by("name"),
    )
    context = _list_context(
        page_title="Equipamentos",
        page_description="Armas, armaduras e equipamentos de aventura com custo e peso.",
        filterset=filtered,
    )
    context["filtered_equipment"] = filtered
    return render(request, "sdr/equipment_list.html", context)


def equipment(request, pk):
    obj = get_object_or_404(SDR_Equipment.objects.using("sdr"), id=pk)
    primary_rows = _rows(
        ("Família", obj.family),
        ("Categoria", obj.category),
        ("Subcategoria", obj.subcategory),
        ("Tipo", obj.type),
        ("Custo", obj.cost),
        ("Peso", obj.weight),
        ("Dano (P)", obj.dmg_s),
        ("Dano (M)", obj.dmg_m),
        ("Crítico", obj.critical),
        ("Incremento de Alcance", obj.range_increment),
        ("Bônus de Armadura/Escudo", obj.armor_shield_bonus),
        ("Bônus Máx. de Destreza", obj.maximum_dex_bonus),
        ("Penalidade de Armadura", obj.armor_check_penalty),
        ("Falha Arcana", obj.arcane_spell_failure_chance),
        ("Deslocamento 9 m", obj.speed_30),
        ("Deslocamento 6 m", obj.speed_20),
    )
    context = _detail_context(
        page_title="Equipamentos",
        category_title="Equipamentos",
        category_url_name="sdr:equipment",
        object_name=obj.name,
        detail_title=obj.name,
        detail_subtitle=_join_bits(obj.family, obj.category, obj.type),
        summary_rows=primary_rows,
        text_sections=[],
        fallback_full_text=_full_text_fallback(obj, primary_rows),
    )
    return render(request, "sdr/equipment.html", context)


def feats(request):
    filtered = FeatFilter(
        request.GET,
        queryset=SDR_Feat.objects.using("sdr").order_by("name"),
    )
    context = _list_context(
        page_title="Talentos",
        page_description="Pré-requisitos, benefícios e observações especiais em formato de consulta.",
        filterset=filtered,
    )
    context["filtered_feats"] = filtered
    return render(request, "sdr/feats.html", context)


def feat(request, pk):
    obj = get_object_or_404(SDR_Feat.objects.using("sdr"), id=pk)
    primary_rows = _rows(
        ("Tipo", obj.type),
        ("Pré-requisito", obj.prerequisite),
    )
    text_sections = _text_blocks(
        ("Benefício", obj.benefit),
        ("Normal", obj.normal),
        ("Especial", obj.special),
    )
    context = _detail_context(
        page_title="Talentos",
        category_title="Talentos",
        category_url_name="sdr:feats",
        object_name=obj.name,
        detail_title=obj.name,
        detail_subtitle=obj.type,
        summary_rows=primary_rows,
        text_sections=text_sections,
        fallback_full_text=_full_text_fallback(obj, primary_rows, text_sections),
    )
    return render(request, "sdr/feat.html", context)


def items(request):
    filtered = ItemFilter(
        request.GET,
        queryset=SDR_Item.objects.using("sdr").order_by("name"),
    )
    context = _list_context(
        page_title="Itens Mágicos",
        page_description="Auras, preços e pré-requisitos dos itens mágicos do SRD.",
        filterset=filtered,
    )
    context["filtered_items"] = filtered
    return render(request, "sdr/items.html", context)


def item(request, pk):
    obj = get_object_or_404(SDR_Item.objects.using("sdr"), id=pk)
    primary_rows = _rows(
        ("Categoria", obj.category),
        ("Subcategoria", obj.subcategory),
        ("Aura", obj.aura),
        ("Nível de Conjurador", obj.caster_level),
        ("Preço", obj.price),
        ("Custo", obj.cost),
        ("Peso", obj.weight),
    )
    text_sections = _text_blocks(
        ("Habilidade Especial", obj.special_ability),
        ("Pré-requisitos", obj.prereq),
    )
    context = _detail_context(
        page_title="Itens Mágicos",
        category_title="Itens Mágicos",
        category_url_name="sdr:items",
        object_name=obj.name,
        detail_title=obj.name,
        detail_subtitle=_join_bits(obj.category, obj.subcategory),
        summary_rows=primary_rows,
        text_sections=text_sections,
        fallback_full_text=_full_text_fallback(obj, primary_rows, text_sections),
    )
    return render(request, "sdr/item.html", context)


def powers(request):
    filtered = PowerFilter(
        request.GET,
        queryset=SDR_Power.objects.using("sdr").order_by("name"),
    )
    context = _list_context(
        page_title="Poderes Psiônicos",
        page_description="Disciplinas, alcance e custo em pontos de poder em leitura rápida.",
        filterset=filtered,
    )
    context["filtered_powers"] = filtered
    return render(request, "sdr/powers.html", context)


def power(request, pk):
    obj = get_object_or_404(SDR_Power.objects.using("sdr"), id=pk)
    primary_rows = _rows(
        ("Disciplina", obj.discipline),
        ("Subdisciplina", obj.subdiscipline),
        ("Descritor", obj.descriptor),
        ("Nível", obj.level),
        ("Exibição", obj.display),
        ("Tempo de Manifestação", obj.manifesting_time),
        ("Alcance", obj.range),
        ("Alvo", obj.target),
        ("Área", obj.area),
        ("Efeito", obj.effect),
        ("Duração", obj.duration),
        ("Teste de Resistência", obj.saving_throw),
        ("Pontos de Poder", obj.power_points),
        ("Resistência a Poderes", obj.power_resistance),
    )
    text_sections = _text_blocks(
        ("Resumo", obj.short_description),
        ("Descrição", obj.description),
        ("Aprimoramento", obj.augment),
        ("Custo em XP", obj.xp_cost),
    )
    context = _detail_context(
        page_title="Poderes Psiônicos",
        category_title="Poderes Psiônicos",
        category_url_name="sdr:powers",
        object_name=obj.name,
        detail_title=obj.name,
        detail_subtitle=_join_bits(obj.discipline, obj.level),
        summary_rows=primary_rows,
        text_sections=text_sections,
        fallback_full_text=_full_text_fallback(obj, primary_rows, text_sections),
    )
    return render(request, "sdr/power.html", context)


def skills(request):
    filtered = SkillFilter(
        request.GET,
        queryset=SDR_Skill.objects.using("sdr").order_by("name"),
    )
    context = _list_context(
        page_title="Perícias",
        page_description="Uso, habilidade-chave e interações especiais das perícias.",
        filterset=filtered,
    )
    context["filtered_skills"] = filtered
    return render(request, "sdr/skills.html", context)


def skill(request, pk):
    obj = get_object_or_404(SDR_Skill.objects.using("sdr"), id=pk)
    primary_rows = _rows(
        ("Habilidade-chave", obj.key_ability),
        ("Treinada", obj.trained),
        ("Penalidade de Armadura", obj.armor_check),
        ("Psíquica", obj.psionic),
    )
    text_sections = _text_blocks(
        ("Descrição", obj.description),
        ("Teste de Perícia", obj.skill_check),
        ("Ação", obj.action),
        ("Tentar Novamente", obj.try_again),
        ("Especial", obj.special),
        ("Sinergia", obj.synergy),
        ("Uso sem Treino", obj.untrained),
    )
    context = _detail_context(
        page_title="Perícias",
        category_title="Perícias",
        category_url_name="sdr:skills",
        object_name=obj.name,
        detail_title=obj.name,
        detail_subtitle=obj.key_ability,
        summary_rows=primary_rows,
        text_sections=text_sections,
        fallback_full_text=_full_text_fallback(obj, primary_rows, text_sections),
    )
    return render(request, "sdr/skill.html", context)
