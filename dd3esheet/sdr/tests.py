import json
import tempfile
import os
from django.test import TestCase
from django.core.management import call_command
from django.db import connections
from django.urls import reverse
from sdr.lookups import resolve_spell
from sdr.models import (
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


class SDRViewsTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpTestData(cls):
        with connections['sdr'].cursor() as cursor:
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    altname TEXT,
                    school TEXT,
                    subschool TEXT,
                    descriptor TEXT,
                    spellcraft_dc TEXT,
                    level TEXT,
                    components TEXT,
                    casting_time TEXT,
                    range TEXT,
                    target TEXT,
                    area TEXT,
                    effect TEXT,
                    duration TEXT,
                    saving_throw TEXT,
                    spell_resistance TEXT,
                    short_description TEXT,
                    to_develop TEXT,
                    material_components TEXT,
                    arcane_material_components TEXT,
                    focus TEXT,
                    description TEXT,
                    xp_cost TEXT,
                    arcane_focus TEXT,
                    wizard_focus TEXT,
                    verbal_components TEXT,
                    sorcerer_focus TEXT,
                    bard_focus TEXT,
                    cleric_focus TEXT,
                    druid_focus TEXT,
                    full_text TEXT,
                    reference TEXT
                );
                CREATE TABLE IF NOT EXISTS monster (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    family TEXT,
                    name TEXT NOT NULL,
                    altname TEXT,
                    size TEXT,
                    type TEXT,
                    descriptor TEXT,
                    hit_dice TEXT,
                    initiative TEXT,
                    speed TEXT,
                    armor_class TEXT,
                    base_attack TEXT,
                    grapple TEXT,
                    attack TEXT,
                    full_attack TEXT,
                    space TEXT,
                    reach TEXT,
                    special_attacks TEXT,
                    special_qualities TEXT,
                    saves TEXT,
                    abilities TEXT,
                    skills TEXT,
                    bonus_feats TEXT,
                    feats TEXT,
                    epic_feats TEXT,
                    environment TEXT,
                    organization TEXT,
                    challenge_rating TEXT,
                    treasure TEXT,
                    alignment TEXT,
                    advancement TEXT,
                    level_adjustment TEXT,
                    special_abilities TEXT,
                    stat_block TEXT,
                    full_text TEXT,
                    reference TEXT
                );
                CREATE TABLE IF NOT EXISTS class (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT,
                    alignment TEXT,
                    hit_die TEXT,
                    class_skills TEXT,
                    skill_points TEXT,
                    skill_points_ability TEXT,
                    spell_stat TEXT,
                    proficiencies TEXT,
                    spell_type TEXT,
                    epic_feat_base_level TEXT,
                    epic_feat_interval TEXT,
                    epic_feat_list TEXT,
                    epic_full_text TEXT,
                    req_race TEXT,
                    req_weapon_proficiency TEXT,
                    req_base_attack_bonus TEXT,
                    req_skill TEXT,
                    req_feat TEXT,
                    req_spells TEXT,
                    req_languages TEXT,
                    req_psionics TEXT,
                    req_epic_feat TEXT,
                    req_special TEXT,
                    spell_list_1 TEXT,
                    spell_list_2 TEXT,
                    spell_list_3 TEXT,
                    spell_list_4 TEXT,
                    spell_list_5 TEXT,
                    full_text TEXT,
                    reference TEXT
                );
                CREATE TABLE IF NOT EXISTS class_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    level TEXT,
                    base_attack_bonus TEXT,
                    fort_save TEXT,
                    ref_save TEXT,
                    will_save TEXT,
                    caster_level TEXT,
                    points_per_day TEXT,
                    ac_bonus TEXT,
                    flurry_of_blows TEXT,
                    bonus_spells TEXT,
                    powers_known TEXT,
                    unarmored_speed_bonus TEXT,
                    unarmed_damage TEXT,
                    power_level TEXT,
                    special TEXT,
                    slots_0 TEXT,
                    slots_1 TEXT,
                    slots_2 TEXT,
                    slots_3 TEXT,
                    slots_4 TEXT,
                    slots_5 TEXT,
                    slots_6 TEXT,
                    slots_7 TEXT,
                    slots_8 TEXT,
                    slots_9 TEXT,
                    spells_known_0 TEXT,
                    spells_known_1 TEXT,
                    spells_known_2 TEXT,
                    spells_known_3 TEXT,
                    spells_known_4 TEXT,
                    spells_known_5 TEXT,
                    spells_known_6 TEXT,
                    spells_known_7 TEXT,
                    spells_known_8 TEXT,
                    spells_known_9 TEXT,
                    reference TEXT
                );
                CREATE TABLE IF NOT EXISTS domain (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    granted_powers TEXT,
                    spell_1 TEXT,
                    spell_2 TEXT,
                    spell_3 TEXT,
                    spell_4 TEXT,
                    spell_5 TEXT,
                    spell_6 TEXT,
                    spell_7 TEXT,
                    spell_8 TEXT,
                    spell_9 TEXT,
                    full_text TEXT,
                    reference TEXT
                );
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    family TEXT,
                    category TEXT,
                    subcategory TEXT,
                    cost TEXT,
                    dmg_s TEXT,
                    armor_shield_bonus TEXT,
                    maximum_dex_bonus TEXT,
                    dmg_m TEXT,
                    weight TEXT,
                    critical TEXT,
                    armor_check_penalty TEXT,
                    arcane_spell_failure_chance TEXT,
                    range_increment TEXT,
                    speed_30 TEXT,
                    type TEXT,
                    speed_20 TEXT,
                    full_text TEXT,
                    reference TEXT
                );
                CREATE TABLE IF NOT EXISTS feat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT,
                    multiple TEXT,
                    stack TEXT,
                    choice TEXT,
                    prerequisite TEXT,
                    benefit TEXT,
                    normal TEXT,
                    special TEXT,
                    full_text TEXT,
                    reference TEXT
                );
                CREATE TABLE IF NOT EXISTS item (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    subcategory TEXT,
                    special_ability TEXT,
                    aura TEXT,
                    caster_level TEXT,
                    price TEXT,
                    manifester_level TEXT,
                    prereq TEXT,
                    cost TEXT,
                    weight TEXT,
                    full_text TEXT,
                    reference TEXT
                );
                CREATE TABLE IF NOT EXISTS power (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    discipline TEXT,
                    subdiscipline TEXT,
                    descriptor TEXT,
                    level TEXT,
                    display TEXT,
                    manifesting_time TEXT,
                    range TEXT,
                    target TEXT,
                    area TEXT,
                    effect TEXT,
                    duration TEXT,
                    saving_throw TEXT,
                    power_points TEXT,
                    power_resistance TEXT,
                    short_description TEXT,
                    xp_cost TEXT,
                    description TEXT,
                    augment TEXT,
                    full_text TEXT,
                    reference TEXT
                );
                CREATE TABLE IF NOT EXISTS skill (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    subtype TEXT,
                    key_ability TEXT,
                    psionic TEXT,
                    trained TEXT,
                    armor_check TEXT,
                    description TEXT,
                    skill_check TEXT,
                    action TEXT,
                    try_again TEXT,
                    special TEXT,
                    restriction TEXT,
                    synergy TEXT,
                    epic_use TEXT,
                    untrained TEXT,
                    full_text TEXT,
                    reference TEXT
                );
            """)

        cls.spell = SDR_Spell.objects.using('sdr').create(
            name="Misseis Magicos",
            altname="Magic Missile",
            school="Evocacao",
            level="Mago 1",
            components="V, S",
            casting_time="1 acao padrao",
            range="Medio",
            target="Uma criatura",
            duration="Instantanea",
            saving_throw="Nenhum",
            spell_resistance="Sim",
            short_description="Setas de energia acertam automaticamente.",
            description="A magia dispara projeteis de energia contra o alvo.",
        )
        SDR_Spell.objects.using('sdr').create(
            name="Armadura Arcana",
            school="Abjuracao",
            level="Mago 1",
            components="V, S, F",
            short_description="Campo de forca protege o conjurador.",
        )

        cls.monster = SDR_Monster.objects.using('sdr').create(
            name="Urso-Coruja",
            family="Bestas",
            size="Grande",
            type="Magico",
            hit_dice="5d8+15",
            initiative="+1",
            speed="9 m",
            armor_class="15",
            base_attack="+3",
            grapple="+11",
            attack="Garra +6",
            full_attack="2 garras +6 e mordida +1",
            space="3 m",
            reach="1,5 m",
            special_attacks="Agarrar aprimorado",
            special_qualities="Visao na penumbra",
            saves="Fort +7, Ref +2, Vont +2",
            abilities="For 21, Des 12, Con 17, Int 2, Sab 12, Car 10",
            skills="Ouvir +8, Observar +8",
            feats="Alerta, Foco em Arma",
            environment="Florestas temperadas",
            organization="Solitario",
            challenge_rating="4",
            treasure="Nenhum",
            alignment="Sempre neutro",
            advancement="6-8 DV",
            level_adjustment="-",
            full_text="Criatura feroz com corpo de urso e cabeca de coruja.",
        )

        cls.dnd_class = SDR_Class.objects.using('sdr').create(
            name="Mago",
            type="Base",
            alignment="Qualquer",
            hit_die="d4",
            class_skills="Concentracao, Conhecimento, Oficio",
            skill_points="2",
            skill_points_ability="Inteligencia",
            proficiencies="Cajados, adagas e bestas leves.",
            spell_stat="Inteligencia",
            spell_type="Arcana",
            full_text="Mestres das artes arcanas.",
        )
        SDR_ClassTable.objects.using('sdr').create(
            name="Mago",
            level="1",
            base_attack_bonus="+0",
            fort_save="+0",
            ref_save="+0",
            will_save="+2",
            special="Escrever Pergaminho",
            slots_0="3",
            slots_1="1",
        )

        cls.domain = SDR_Domain.objects.using('sdr').create(
            name="Fogo",
            granted_powers="Voce pode expulsar criaturas da agua com mais facilidade.",
            spell_1="Maos Flamejantes",
            spell_2="Esquentar Metal",
            spell_3="Bola de Fogo",
            full_text="Dominio dedicado ao elemento fogo.",
        )

        cls.equipment = SDR_Equipment.objects.using('sdr').create(
            name="Espada Longa",
            family="Arma",
            category="Corpo a corpo",
            subcategory="Marcial",
            type="Cortante",
            cost="15 PO",
            weight="4 lb",
            dmg_s="1d6",
            dmg_m="1d8",
            critical="19-20/x2",
            range_increment="-",
            full_text="Arma marcial comum entre aventureiros.",
        )

        cls.feat = SDR_Feat.objects.using('sdr').create(
            name="Ataque Poderoso",
            type="Geral",
            prerequisite="For 13",
            benefit="Troca bonus de ataque por dano adicional.",
            normal="Sem o talento, a troca nao e permitida.",
            special="Pode ser usado com ataques corpo a corpo.",
            full_text="Talento classico de combate.",
        )

        cls.item = SDR_Item.objects.using('sdr').create(
            name="Mochila Util",
            category="Item Maravilhoso",
            subcategory="Utilidade",
            aura="Fraca conjuracao",
            caster_level="9",
            price="2.000 PO",
            cost="1.000 PO",
            weight="2 lb",
            prereq="Criar Item Maravilhoso",
            special_ability="Espaco extradimensional",
            full_text="Armazena muito mais do que aparenta.",
        )

        cls.power = SDR_Power.objects.using('sdr').create(
            name="Raio de Energia",
            discipline="Psicocinese",
            subdiscipline="Energia",
            descriptor="Eletricidade",
            level="Psion 2",
            display="Visual",
            manifesting_time="1 acao padrao",
            range="Medio",
            effect="Raio",
            duration="Instantanea",
            saving_throw="Nenhum",
            power_points="3",
            power_resistance="Sim",
            short_description="Um raio de energia atinge o alvo.",
            description="Voce dispara energia psionica concentrada.",
            augment="Mais pontos aumentam o dano.",
        )

        cls.skill = SDR_Skill.objects.using('sdr').create(
            name="Acrobacia",
            key_ability="Destreza",
            trained="Nao",
            armor_check="Sim",
            description="Permite equilibrar-se e executar saltos curtos.",
            skill_check="CD varia conforme a manobra.",
            action="Normalmente parte do movimento.",
            try_again="Sim",
            special="Sinergia com Saltar.",
            synergy="+2 em certas manobras.",
            untrained="Voce pode usar sem treinamento.",
        )

    def test_home_and_lists_render_portuguese_titles(self):
        cases = [
            ('sdr:home', 'Referência — D&amp;D 3.5', 'sdr/home.html'),
            ('sdr:spells', 'Magias', 'sdr/spells.html'),
            ('sdr:monsters', 'Monstros', 'sdr/monsters.html'),
            ('sdr:classes', 'Classes', 'sdr/classes.html'),
            ('sdr:domains', 'Domínios', 'sdr/domains.html'),
            ('sdr:equipment', 'Equipamentos', 'sdr/equipment_list.html'),
            ('sdr:feats', 'Talentos', 'sdr/feats.html'),
            ('sdr:items', 'Itens Mágicos', 'sdr/items.html'),
            ('sdr:powers', 'Poderes Psiônicos', 'sdr/powers.html'),
            ('sdr:skills', 'Perícias', 'sdr/skills.html'),
        ]

        for url_name, expected_title, template_name in cases:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_title)
                self.assertTemplateUsed(response, template_name)

    def test_detail_pages_render_structured_portuguese_labels(self):
        cases = [
            ('sdr:spell', self.spell.id, 'Misseis Magicos', 'Escola'),
            ('sdr:monster', self.monster.id, 'Urso-Coruja', 'Dados de Vida'),
            ('sdr:class', self.dnd_class.id, 'Mago', 'Dado de Vida'),
            ('sdr:domain', self.domain.id, 'Fogo', 'Poderes Concedidos'),
            ('sdr:equipment_detail', self.equipment.id, 'Espada Longa', 'Custo'),
            ('sdr:feat', self.feat.id, 'Ataque Poderoso', 'Benefício'),
            ('sdr:item', self.item.id, 'Mochila Util', 'Preço'),
            ('sdr:power', self.power.id, 'Raio de Energia', 'Disciplina'),
            ('sdr:skill', self.skill.id, 'Acrobacia', 'Habilidade-chave'),
        ]

        for url_name, pk, expected_name, expected_label in cases:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, args=[pk]))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_name)
                self.assertContains(response, expected_label)

    def test_class_detail_includes_progression_table(self):
        response = self.client.get(reverse('sdr:class', args=[self.dnd_class.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tabela de Progressão')
        self.assertContains(response, 'BBA')
        self.assertContains(response, 'Escrever Pergaminho')

    def test_domain_detail_lists_granted_spells(self):
        response = self.client.get(reverse('sdr:domain', args=[self.domain.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Magias Concedidas')
        self.assertContains(response, '1º círculo')
        self.assertContains(response, 'Bola de Fogo')

    def test_missing_detail_returns_404(self):
        cases = [
            'sdr:spell',
            'sdr:monster',
            'sdr:class',
            'sdr:domain',
            'sdr:equipment_detail',
            'sdr:feat',
            'sdr:item',
            'sdr:power',
            'sdr:skill',
        ]

        for url_name in cases:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, args=[999999]))
                self.assertEqual(response.status_code, 404)

    def test_spell_filter_reduces_results_and_keeps_expected_item(self):
        base_response = self.client.get(reverse('sdr:spells'))
        filtered_response = self.client.get(reverse('sdr:spells'), {'name': 'Misseis Magicos'})

        self.assertEqual(base_response.status_code, 200)
        self.assertEqual(filtered_response.status_code, 200)
        self.assertGreater(base_response.context['filtered_spells'].qs.count(), 1)
        self.assertEqual(filtered_response.context['filtered_spells'].qs.count(), 1)
        self.assertContains(filtered_response, 'Misseis Magicos')
        self.assertNotContains(filtered_response, 'Armadura Arcana')

class SDRFeatTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Cria a tabela 'feat' no banco de testes 'sdr' pois possui managed = False
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT,
                    multiple TEXT,
                    stack TEXT,
                    choice TEXT,
                    prerequisite TEXT,
                    benefit TEXT,
                    normal TEXT,
                    special TEXT,
                    full_text TEXT,
                    reference TEXT
                );
            """)

    def test_import_feats_command(self):
        # Cria um arquivo JSON temporario para testar
        temp_data = [
            {
                "name": "Ataque Especial Teste",
                "type": "General",
                "prerequisite": "Nenhum",
                "benefit": "Concede +2 de dano de teste.",
                "reference": "Livro de Teste (PT)"
            }
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w+', delete=False, encoding='utf-8') as f:
            json.dump(temp_data, f)
            temp_file_path = f.name

        try:
            # Chama o comando passando o arquivo temporario
            call_command('import_feats', file=temp_file_path)
            
            # Verifica se foi criado com sucesso no banco sdr
            qs = SDR_Feat.objects.using('sdr').filter(name="Ataque Especial Teste")
            self.assertTrue(qs.exists())
            feat = qs.first()
            self.assertEqual(feat.benefit, "Concede +2 de dano de teste.")
            self.assertEqual(feat.reference, "Livro de Teste (PT)")
            
            # Testa a atualizacao do talento
            temp_data[0]["benefit"] = "Concede +4 de dano de teste atualizado."
            with open(temp_file_path, 'w', encoding='utf-8') as f_write:
                json.dump(temp_data, f_write)
                
            call_command('import_feats', file=temp_file_path)
            
            feat.refresh_from_db(using='sdr')
            self.assertEqual(feat.benefit, "Concede +4 de dano de teste atualizado.")
            
        finally:
            # Garante a limpeza do banco de testes e do arquivo
            SDR_Feat.objects.using('sdr').filter(name="Ataque Especial Teste").delete()
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


class SDRSpellTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Cria a tabela 'spell' no banco de testes 'sdr' pois possui managed = False
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    altname TEXT,
                    school TEXT,
                    subschool TEXT,
                    descriptor TEXT,
                    spellcraft_dc TEXT,
                    level TEXT,
                    components TEXT,
                    casting_time TEXT,
                    range TEXT,
                    target TEXT,
                    area TEXT,
                    effect TEXT,
                    duration TEXT,
                    saving_throw TEXT,
                    spell_resistance TEXT,
                    short_description TEXT,
                    to_develop TEXT,
                    material_components TEXT,
                    arcane_material_components TEXT,
                    focus TEXT,
                    description TEXT,
                    xp_cost TEXT,
                    arcane_focus TEXT,
                    wizard_focus TEXT,
                    verbal_components TEXT,
                    sorcerer_focus TEXT,
                    bard_focus TEXT,
                    cleric_focus TEXT,
                    druid_focus TEXT,
                    full_text TEXT,
                    reference TEXT
                );
            """)

    def test_import_spells_command(self):
        # 1. Cadastra uma magia ficticia original em ingles na base de testes
        original_spell = SDR_Spell(
            name="Magic Missile",
            school="Evocation",
            level="Sor/Wiz 1",
            description="An original English description."
        )
        original_spell.save(using='sdr')

        # 2. Cria um arquivo JSON temporario contendo a traducao em portugues
        temp_data = [
            {
                "name": "Misseis Magicos",
                "altname": "Magic Missile",
                "school": "Evocation",
                "level": "Sor/Wiz 1",
                "description": "Uma descricao traduzida em portugues.",
                "reference": "Livro do Jogador (PT)"
            }
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w+', delete=False, encoding='utf-8') as f:
            json.dump(temp_data, f)
            temp_file_path = f.name

        try:
            # 3. Executa o comando de importacao
            call_command('import_spells', file=temp_file_path)
            
            # 4. Verifica se a magia original em ingles foi traduzida in-place
            qs = SDR_Spell.objects.using('sdr').filter(altname="Magic Missile")
            self.assertTrue(qs.exists())
            self.assertEqual(qs.count(), 1) # Sem duplicatas!
            
            spell = qs.first()
            self.assertEqual(spell.name, "Misseis Magicos")
            self.assertEqual(spell.description, "Uma descricao traduzida em portugues.")
            self.assertEqual(spell.reference, "Livro do Jogador (PT)")
            
        finally:
            # Garante limpeza
            SDR_Spell.objects.using('sdr').filter(name="Misseis Magicos").delete()
            SDR_Spell.objects.using('sdr').filter(name="Magic Missile").delete()
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


class ResolveSpellTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    altname TEXT,
                    school TEXT, subschool TEXT, descriptor TEXT,
                    spellcraft_dc TEXT, level TEXT, components TEXT,
                    casting_time TEXT, range TEXT, target TEXT, area TEXT,
                    effect TEXT, duration TEXT, saving_throw TEXT,
                    spell_resistance TEXT, short_description TEXT,
                    to_develop TEXT, material_components TEXT,
                    arcane_material_components TEXT, focus TEXT,
                    description TEXT, xp_cost TEXT,
                    arcane_focus TEXT, wizard_focus TEXT,
                    verbal_components TEXT, sorcerer_focus TEXT,
                    bard_focus TEXT, cleric_focus TEXT, druid_focus TEXT,
                    full_text TEXT, reference TEXT
                );
            """)

    def setUp(self):
        SDR_Spell.objects.using('sdr').all().delete()
        SDR_Spell(name="Magic Missile", altname="Misseis Magicos",
                  school="Evocation", level="Sor/Wiz 1").save(using='sdr')

    def test_match_by_name_case_insensitive(self):
        self.assertEqual(resolve_spell("magic missile").name, "Magic Missile")
        self.assertEqual(resolve_spell("MAGIC MISSILE").name, "Magic Missile")

    def test_match_by_altname_when_name_misses(self):
        self.assertEqual(resolve_spell("Misseis Magicos").name, "Magic Missile")

    def test_returns_none_for_empty(self):
        self.assertIsNone(resolve_spell(""))
        self.assertIsNone(resolve_spell(None))
        self.assertIsNone(resolve_spell("   "))

    def test_returns_none_for_unknown(self):
        self.assertIsNone(resolve_spell("Bola de Fogo Tropical"))

    def test_ambiguity_returns_first_by_id(self):
        first = SDR_Spell.objects.using('sdr').get(name="Magic Missile")
        duplicate = SDR_Spell(name="Magic Missile", school="X")
        duplicate.save(using='sdr')
        result = resolve_spell("Magic Missile")
        self.assertEqual(result.id, first.id)
        self.assertEqual(result.school, "Evocation")
