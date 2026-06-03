from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.db import connections
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import (
    Character, CharacterStats, CharacterStatus, CharacterSavingThrows,
    CharacterAttackModifiers, CharacterSkillGraduation, CharacterOtherItemObs,
    CharacterMoney, CharacterProgress, CharacterSpellSave, CharacterArcaneSpellFailCheck,
    CharacterMagicConditionalModifiers, CharacterSkill, CharacterWeapon,
    CharacterArmor, CharacterShield, CharacterProtectionItem, CharacterOtherItem,
    CharacterSpellcasting, CharacterSpellSlot, CharacterSpell, CharacterFeat,
    CharacterMagicDayUse, CharacterSummon,
    CharacterCompanion, CharacterContact, CharacterContract, CharacterFaction,
    CharacterDailyResource, CharacterActiveEffect, CharacterBuff, CharacterDailyNotes,
)
from sdr.models import SDR_Class, SDR_Monster


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username='alice', password='pass'):
    return User.objects.create_user(username=username, password=password)


def make_character(user, name='Test'):
    return Character.objects.create(User=user, Name=name)


_PHB_CORE_CLASSES = [
    'Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter',
    'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer', 'Wizard',
]


def setup_sdr_class_table():
    """Create the SDR class table and populate it with PHB core classes for testing."""
    with connections['sdr'].cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS class (
                id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                name varchar(999) NOT NULL,
                type varchar(999) NULL,
                alignment varchar(999) NULL,
                hit_die varchar(999) NULL,
                class_skills text NULL,
                skill_points varchar(999) NULL,
                skill_points_ability varchar(999) NULL,
                spell_stat varchar(999) NULL,
                proficiencies text NULL,
                spell_type varchar(999) NULL,
                epic_feat_base_level varchar(999) NULL,
                epic_feat_interval varchar(999) NULL,
                epic_feat_list text NULL,
                epic_full_text text NULL,
                req_race varchar(999) NULL,
                req_weapon_proficiency varchar(999) NULL,
                req_base_attack_bonus varchar(999) NULL,
                req_skill varchar(999) NULL,
                req_feat varchar(999) NULL,
                req_spells varchar(999) NULL,
                req_languages varchar(999) NULL,
                req_psionics varchar(999) NULL,
                req_epic_feat varchar(999) NULL,
                req_special varchar(999) NULL,
                spell_list_1 text NULL,
                spell_list_2 varchar(999) NULL,
                spell_list_3 varchar(999) NULL,
                spell_list_4 varchar(999) NULL,
                spell_list_5 varchar(999) NULL,
                full_text text NULL,
                reference varchar(999) NULL
            )
        """)
        cursor.execute("DELETE FROM class")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS class_table (
                id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                name varchar(999) NOT NULL,
                level varchar(999) NULL,
                base_attack_bonus varchar(999) NULL,
                fort_save varchar(999) NULL,
                ref_save varchar(999) NULL,
                will_save varchar(999) NULL,
                caster_level varchar(999) NULL,
                points_per_day varchar(999) NULL,
                ac_bonus varchar(999) NULL,
                flurry_of_blows varchar(999) NULL,
                bonus_spells varchar(999) NULL,
                powers_known varchar(999) NULL,
                unarmored_speed_bonus varchar(999) NULL,
                unarmed_damage varchar(999) NULL,
                power_level varchar(999) NULL,
                special varchar(999) NULL,
                slots_0 varchar(999) NULL,
                slots_1 varchar(999) NULL,
                slots_2 varchar(999) NULL,
                slots_3 varchar(999) NULL,
                slots_4 varchar(999) NULL,
                slots_5 varchar(999) NULL,
                slots_6 varchar(999) NULL,
                slots_7 varchar(999) NULL,
                slots_8 varchar(999) NULL,
                slots_9 varchar(999) NULL,
                spells_known_0 varchar(999) NULL,
                spells_known_1 varchar(999) NULL,
                spells_known_2 varchar(999) NULL,
                spells_known_3 varchar(999) NULL,
                spells_known_4 varchar(999) NULL,
                spells_known_5 varchar(999) NULL,
                spells_known_6 varchar(999) NULL,
                spells_known_7 varchar(999) NULL,
                spells_known_8 varchar(999) NULL,
                spells_known_9 varchar(999) NULL,
                reference varchar(999) NULL
            )
        """)
        cursor.execute("DELETE FROM class_table")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domain (
                id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                name varchar(999) NOT NULL,
                granted_powers text NULL,
                spell_1 varchar(999) NULL,
                spell_2 varchar(999) NULL,
                spell_3 varchar(999) NULL,
                spell_4 varchar(999) NULL,
                spell_5 varchar(999) NULL,
                spell_6 varchar(999) NULL,
                spell_7 varchar(999) NULL,
                spell_8 varchar(999) NULL,
                spell_9 varchar(999) NULL,
                full_text text NULL,
                reference varchar(999) NULL
            )
        """)
        cursor.execute("DELETE FROM domain")
    SDR_Class.objects.using('sdr').bulk_create(
        [SDR_Class(name=c) for c in _PHB_CORE_CLASSES]
    )
    with connections['sdr'].cursor() as cursor:
        for cls in ['Wizard', 'Sorcerer', 'Cleric', 'Druid']:
            known_0 = '4' if cls == 'Sorcerer' else 'None'
            known_1 = '2' if cls == 'Sorcerer' else 'None'
            cursor.execute(
                "INSERT INTO class_table (name, level, slots_0, slots_1, spells_known_0, spells_known_1) VALUES (?, ?, ?, ?, ?, ?)",
                [cls, '1', '3', '1+1' if cls == 'Cleric' else '1', known_0, known_1],
            )
        cursor.execute(
            "INSERT INTO domain (name, spell_1, spell_2) VALUES (?, ?, ?)",
            ['Healing', 'cure light wounds', 'cure moderate wounds'],
        )


def setup_sdr_spell_table():
    """Create the SDR spell table for testing (unmanaged model)."""
    with connections['sdr'].cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spell (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, altname TEXT,
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
            )
        """)


def setup_sdr_monster_table():
    with connections['sdr'].cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monster (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family TEXT NULL,
                name TEXT NOT NULL,
                altname TEXT NULL,
                size TEXT NULL,
                type TEXT NULL,
                descriptor TEXT NULL,
                hit_dice TEXT NULL,
                initiative TEXT NULL,
                speed TEXT NULL,
                armor_class TEXT NULL,
                base_attack TEXT NULL,
                grapple TEXT NULL,
                attack TEXT NULL,
                full_attack TEXT NULL,
                space TEXT NULL,
                reach TEXT NULL,
                special_attacks TEXT NULL,
                special_qualities TEXT NULL,
                saves TEXT NULL,
                abilities TEXT NULL,
                skills TEXT NULL,
                bonus_feats TEXT NULL,
                feats TEXT NULL,
                epic_feats TEXT NULL,
                environment TEXT NULL,
                organization TEXT NULL,
                challenge_rating TEXT NULL,
                treasure TEXT NULL,
                alignment TEXT NULL,
                advancement TEXT NULL,
                level_adjustment TEXT NULL,
                special_abilities TEXT NULL,
                stat_block TEXT NULL,
                full_text TEXT NULL,
                reference TEXT NULL
            )
        """)


# ---------------------------------------------------------------------------
# Phase B — character creation
# ---------------------------------------------------------------------------

class CreateCharacterViewTests(TestCase):

    def setUp(self):
        self.url = reverse('character:create-character')
        self.user = make_user()

    def test_anonymous_post_redirects_to_login(self):
        resp = self.client.post(self.url, {'Name': 'Mulligan'})
        self.assertRedirects(resp, f"{reverse('login')}?next={self.url}", fetch_redirect_response=False)
        self.assertEqual(Character.objects.count(), 0)

    def test_anonymous_get_redirects_to_login(self):
        resp = self.client.get(self.url)
        self.assertRedirects(resp, f"{reverse('login')}?next={self.url}", fetch_redirect_response=False)

    def test_valid_post_creates_character_with_correct_user(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {'Name': 'Mulligan', 'Description': 'Um aventureiro'})
        self.assertEqual(Character.objects.count(), 1)
        char = Character.objects.first()
        self.assertEqual(char.User, self.user)
        self.assertEqual(char.Name, 'Mulligan')
        self.assertRedirects(resp, reverse('character:character', kwargs={'pk': char.pk}), fetch_redirect_response=False)

    def test_valid_post_cannot_set_arbitrary_user(self):
        """Form must not accept User field from POST — it must be request.user."""
        other = make_user('bob')
        self.client.force_login(self.user)
        self.client.post(self.url, {'Name': 'Mulligan', 'User': other.pk})
        char = Character.objects.first()
        self.assertIsNotNone(char)
        self.assertEqual(char.User, self.user)

    def test_post_without_name_returns_form_error(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {'Name': '', 'Description': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Character.objects.count(), 0)

    def test_valid_post_creates_all_siblings(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {'Name': 'Mulligan'})
        char = Character.objects.first()
        self.assertIsNotNone(char)
        self.assertTrue(CharacterStats.objects.filter(Character=char).exists())
        self.assertTrue(CharacterStatus.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSavingThrows.objects.filter(Character=char).exists())
        self.assertTrue(CharacterAttackModifiers.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSkillGraduation.objects.filter(Character=char).exists())
        self.assertTrue(CharacterOtherItemObs.objects.filter(Character=char).exists())
        self.assertTrue(CharacterMoney.objects.filter(Character=char).exists())
        self.assertTrue(CharacterProgress.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSpellSave.objects.filter(Character=char).exists())
        self.assertTrue(CharacterArcaneSpellFailCheck.objects.filter(Character=char).exists())
        self.assertTrue(CharacterMagicConditionalModifiers.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSpellcasting.objects.filter(Character=char).exists())
        self.assertEqual(CharacterSkill.objects.filter(Character=char).count(), 41)


class BootstrapCharacterSiblingsTests(TestCase):

    def test_creates_all_siblings_and_35_skills(self):
        from .services import _bootstrap_character_siblings
        user = make_user()
        char = Character.objects.create(User=user, Name='Solo')
        _bootstrap_character_siblings(char)
        self.assertTrue(CharacterStats.objects.filter(Character=char).exists())
        self.assertTrue(CharacterStatus.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSavingThrows.objects.filter(Character=char).exists())
        self.assertTrue(CharacterAttackModifiers.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSkillGraduation.objects.filter(Character=char).exists())
        self.assertTrue(CharacterOtherItemObs.objects.filter(Character=char).exists())
        self.assertTrue(CharacterMoney.objects.filter(Character=char).exists())
        self.assertTrue(CharacterProgress.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSpellSave.objects.filter(Character=char).exists())
        self.assertTrue(CharacterArcaneSpellFailCheck.objects.filter(Character=char).exists())
        self.assertTrue(CharacterMagicConditionalModifiers.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSpellcasting.objects.filter(Character=char).exists())
        self.assertEqual(CharacterSkill.objects.filter(Character=char).count(), 41)
        self.assertTrue(CharacterSkill.objects.filter(Character=char, SkillName='Escalar').exists())
        self.assertTrue(CharacterSkill.objects.filter(Character=char, SkillName='Esconder-se').exists())
        self.assertEqual(CharacterSkill.objects.filter(Character=char, SkillName='Conhecimento').count(), 3)
        self.assertEqual(CharacterSkill.objects.filter(Character=char, SkillName='Oficios').count(), 3)
        self.assertEqual(CharacterSkill.objects.filter(Character=char, SkillName='Profissao').count(), 3)
        self.assertFalse(CharacterSkill.objects.filter(Character=char, SkillName='Climb').exists())


class CharacterSheetCssTests(TestCase):

    def test_editable_weapon_and_equipment_grid_inputs_have_cell_backgrounds(self):
        css_path = settings.BASE_DIR / 'static' / 'css' / 'character_sheet.css'
        css = css_path.read_text(encoding='utf-8')

        self.assertIn('.attack-card-row > input', css)
        self.assertIn('.attack-meta > input', css)
        self.assertIn('.equipment-card-row > input', css)

    def test_ac_breakdown_labels_stay_below_their_rectangles(self):
        css_path = settings.BASE_DIR / 'static' / 'css' / 'character_sheet.css'
        css = css_path.read_text(encoding='utf-8')

        self.assertIn('.ca-cell {\n    display: flex;\n    flex-direction: column;', css)
        self.assertNotIn('.ca-cell {\n    display: flex;\n    flex-direction: column-reverse;', css)

    def test_spellbook_slot_rows_prioritize_spell_name_space(self):
        css_path = settings.BASE_DIR / 'static' / 'css' / 'character_sheet.css'
        css = css_path.read_text(encoding='utf-8')

        self.assertIn('grid-template-columns: 68px minmax(0, 1fr) 48px;', css)
        self.assertIn('.btn-slot-cast-label', css)
        self.assertIn('font-size: 8px;', css)

# ---------------------------------------------------------------------------
# Phase C — identity inline editing + SDR
# ---------------------------------------------------------------------------

class CharacterIdentityHTMXTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        self.other = make_user('bob')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Test')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})

    def test_htmx_post_identity_saves_and_returns_partial(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {'Name': 'Aragorn', 'Class': 'Ranger', 'Level': '5',
             'Race': 'Human', 'Alignment': 'LG', 'Size': 'M',
             'Deity': '', 'Age': '', 'Sex': '', 'Heigth': '',
             'Weight': '', 'Eye': '', 'Hair': '', 'Skin': ''},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterIdentityForm',
        )
        self.assertEqual(resp.status_code, 200)
        self.char.refresh_from_db()
        self.assertEqual(self.char.Name, 'Aragorn')
        self.assertContains(resp, 'characterIdentityForm')

    def test_htmx_post_identity_by_non_owner_returns_404(self):
        self.client.force_login(self.other)
        resp = self.client.post(
            self.url,
            {'Name': 'Hacker'},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterIdentityForm',
        )
        self.assertEqual(resp.status_code, 404)

    def test_get_character_by_non_owner_returns_404(self):
        self.client.force_login(self.other)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)


class CharacterSheetInlineEditingTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Editable')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})

    def test_stats_table_renders_real_editable_inputs(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="Strength"')
        self.assertContains(resp, 'name="DexterityTemp"')
        # VALOR e MOD TEMPORARIO sao ajustes editaveis que somam ao mod base
        self.assertContains(resp, 'name="StrengthModTemp"')
        self.assertContains(resp, 'hx-target="#characterStatsForm"')

    def test_htmx_post_stats_updates_values_and_returns_partial(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'Strength': '16',
                'Dexterity': '14',
                'Constitution': '12',
                'Intelligence': '10',
                'Wisdom': '8',
                'Charisma': '18',
                'StrengthTemp': '2',
                'StrengthModTemp': '1',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatsForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.char.characterstats.refresh_from_db()
        self.assertEqual(self.char.characterstats.Strength, 16)
        # VALOR e MOD TEMPORARIO persistem como digitados (sao inputs/ajustes)
        self.assertEqual(self.char.characterstats.StrengthTemp, 2)
        self.assertEqual(self.char.characterstats.StrengthModTemp, 1)
        # MOD. DE HABILIDADE = mod(16+2) + 1 = +4 + 1 = +5
        self.assertEqual(self.char.characterstats.StrengthStatMod, 5)
        self.assertContains(resp, 'name="Strength"')

    def test_temporary_adjustments_add_to_modifier_and_cascade(self):
        # VALOR TEMPORARIO e MOD TEMPORARIO sao ajustes que SOMAM ao mod base
        # e cascateiam em agarrar e pericias.
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'Strength': '14', 'Dexterity': '10', 'Constitution': '10',
                'Intelligence': '10', 'Wisdom': '10', 'Charisma': '10',
                'StrengthTemp': '4', 'StrengthModTemp': '1',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatsForm',
        )
        self.assertEqual(resp.status_code, 200)
        stats = self.char.characterstats
        stats.refresh_from_db()
        # FOR base 14 (+2): mod(14+4) + 1 = +4 + 1 = +5
        self.assertEqual(stats.StrengthStatMod, 5)
        # sem ajuste, DES usa o base (mod 10 = 0)
        self.assertEqual(stats.DexterityStatMod, 0)
        # cascata: agarrar usa a FOR efetiva (+5)
        self.char.characterattackmodifiers.refresh_from_db()
        self.assertEqual(self.char.characterattackmodifiers.GrapplerStrModifier, 5)
        # cascata: pericia de FOR (Escalar) usa o mod efetivo
        escalar = CharacterSkill.objects.get(Character=self.char, SkillName='Escalar')
        self.assertEqual(escalar.AbilityModifier, 5)

    def test_htmx_post_stats_recalculates_skills_graduation_and_load(self):
        skill = CharacterSkill.objects.get(Character=self.char, SkillName='Escalar')
        skill.Ranks = 2
        skill.MiscModifier = 1
        skill.save()
        CharacterArmor.objects.create(Character=self.char, Name='Chainmail', Weigth='40 lb')
        CharacterShield.objects.create(Character=self.char, Name='Shield', Weigth='15 lb')
        CharacterOtherItem.objects.create(Character=self.char, Name='Rope', Weigth='10 lb')

        self.char.Level = '5'
        self.char.save()
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'Strength': '16',
                'Dexterity': '14',
                'Constitution': '12',
                'Intelligence': '10',
                'Wisdom': '8',
                'Charisma': '18',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatsForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.char.characterskillgraduation.refresh_from_db()
        self.char.characterotheritemobs.refresh_from_db()
        skill.refresh_from_db()
        self.assertEqual(self.char.characterskillgraduation.MaxGraduation, 8)
        self.assertEqual(self.char.characterskillgraduation.OtherClassMaxGraduation, 4)
        self.assertEqual(skill.AbilityModifier, 3)
        self.assertEqual(skill.SkillModifier, 6)
        self.assertEqual(self.char.characterotheritemobs.LightLoad, 76)
        self.assertEqual(self.char.characterotheritemobs.HeavyLoad, 230)
        self.assertEqual(self.char.characterotheritemobs.TotalWCarried, 65)

    def test_htmx_post_stats_oob_refreshes_dependent_sections(self):
        # Editar um atributo precisa atualizar na tela TODOS os derivados que
        # dependem dele, mesmo os que vivem em outras secoes/partials. Como cada
        # form so troca a si mesmo (hx-target), as secoes irmas voltam como
        # out-of-band swaps (hx-swap-oob) na mesma resposta.
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'Strength': '10', 'Dexterity': '18', 'Constitution': '10',
                'Intelligence': '10', 'Wisdom': '10', 'Charisma': '10',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatsForm',
        )

        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # form editado volta como swap principal
        self.assertContains(resp, 'id="characterStatsForm"')
        # secoes dependentes voltam como out-of-band
        self.assertIn('hx-swap-oob="true"', content)
        self.assertIn('id="characterArmorForm"', content)       # CA depende da Destreza
        self.assertIn('id="characterSavesForm"', content)       # Reflexos depende da Destreza
        self.assertIn('id="characterDefenseSummary"', content)  # Toque/Surpresa/Iniciativa
        self.assertIn('id="characterSkillsForm"', content)      # pericias de Destreza
        # o proprio form editado nao deve voltar duplicado como OOB
        self.assertNotIn('id="characterStatsForm" hx-swap-oob', content)

    def test_skills_render_key_ability_and_specialization_slots(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-derived="SkillAbility"')
        self.assertContains(resp, 'name="skill_', count=None)
        self.assertContains(resp, 'data-field="SkillSpecialization"')
        self.assertContains(resp, 'Conhecimento', count=3)
        self.assertContains(resp, 'Oficios', count=3)
        self.assertContains(resp, 'Profissao', count=3)
        self.assertContains(resp, 'data-derived="SkillTrainedOnly"')

    def test_filling_all_expandable_skill_specializations_adds_one_slot(self):
        self.client.force_login(self.user)
        conhecimentos = list(CharacterSkill.objects.filter(Character=self.char, SkillName='Conhecimento').order_by('id'))
        payload = {}
        for index, skill in enumerate(CharacterSkill.objects.filter(Character=self.char).order_by('id'), start=1):
            payload[f'skill_{index}_SkillName'] = skill.SkillName
            payload[f'skill_{index}_SkillSpecialization'] = ''
            payload[f'skill_{index}_Ranks'] = str(skill.Ranks or 0)
            payload[f'skill_{index}_MiscModifier'] = str(skill.MiscModifier or 0)
            if skill in conhecimentos:
                payload[f'skill_{index}_SkillSpecialization'] = f'Area {conhecimentos.index(skill) + 1}'

        resp = self.client.post(
            self.url,
            payload,
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterSkillsForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CharacterSkill.objects.filter(Character=self.char, SkillName='Conhecimento').count(), 4)
        self.assertContains(resp, 'Area 1')

    def test_trained_only_skill_without_ranks_has_zero_total(self):
        skill = CharacterSkill.objects.get(Character=self.char, SkillName='Operar Mecanismo')
        self.char.characterstats.Intelligence = 16
        self.char.characterstats.save()

        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'Strength': '10',
                'Dexterity': '10',
                'Constitution': '10',
                'Intelligence': '16',
                'Wisdom': '10',
                'Charisma': '10',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatsForm',
        )

        self.assertEqual(resp.status_code, 200)
        skill.refresh_from_db()
        self.assertEqual(skill.AbilityModifier, 3)
        self.assertEqual(skill.SkillModifier, 0)

    def test_htmx_post_equipment_recalculates_armor_class_from_items(self):
        self.char.characterstats.Dexterity = 14
        self.char.characterstats.save()
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'armor_Name': 'Chainmail',
                'armor_Type': 'Media',
                'armor_ACBonus': '+5',
                'armor_MaxDex': '+2',
                'armor_CheckPenalty': '-5',
                'armor_SpellFailure': '30%',
                'armor_Speed': '6 m',
                'armor_Weigth': '40 lb',
                'armor_SpecialProperties': '',
                'shield_Name': 'Heavy Shield',
                'shield_ACBonus': '+2',
                'shield_Weigth': '15 lb',
                'shield_CheckPenalty': '-2',
                'shield_SpellFailure': '15%',
                'shield_SpecialProperties': '',
                'protection_1_Name': 'Ring',
                'protection_1_ACBonus': '+1',
                'protection_1_Weigth': '-',
                'protection_1_SpecialProperties': 'Deflection',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterEquipmentForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.char.characterstatus.refresh_from_db()
        self.assertEqual(self.char.characterstatus.ACArmorBonus, 5)
        self.assertEqual(self.char.characterstatus.ACShieldBonus, 2)
        self.assertEqual(self.char.characterstatus.ACMiscModifier, 1)
        self.assertEqual(self.char.characterstatus.ACTotal, 20)

    def test_htmx_post_weapon_slot_creates_editable_weapon(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'weapon_1_Attack': 'Espada longa',
                'weapon_1_AttackBonus': '+5',
                'weapon_1_Damage': '1d8+3',
                'weapon_1_Critical': '19-20/x2',
                'weapon_1_Range': '',
                'weapon_1_Type': 'Corte',
                'weapon_1_Notes': 'Corpo a corpo',
                'weapon_1_AmmunitionName': '',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatsForm',
        )

        self.assertEqual(resp.status_code, 200)
        weapon = CharacterWeapon.objects.get(Character=self.char)
        self.assertEqual(weapon.Attack, 'Espada longa')
        self.assertEqual(weapon.Damage, '1d8+3')
        # Resposta é agora só o form de atributos; verifica persistência no DB
        self.assertContains(resp, 'id="characterStatsForm"')

    def test_htmx_post_attack_recalculates_melee_and_ranged_weapon_bonuses(self):
        CharacterWeapon.objects.create(
            Character=self.char,
            Name='Espada longa',
            Attack='Espada longa',
            Range='-',
            Type='Corte',
        )
        CharacterWeapon.objects.create(
            Character=self.char,
            Name='Arco curto',
            Attack='Arco curto',
            Range='18 m',
            Type='Perfuracao',
        )
        self.char.characterstats.Strength = 16
        self.char.characterstats.Dexterity = 18
        self.char.characterstats.save()
        self.char.characterstatus.ACSizeModifier = -1
        self.char.characterstatus.save()

        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {'BBA': '6'},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterAttackForm',
        )

        self.assertEqual(resp.status_code, 200)
        weapons = list(CharacterWeapon.objects.filter(Character=self.char).order_by('id'))
        self.assertEqual(weapons[0].AttackBonus, '+8')
        self.assertEqual(weapons[1].AttackBonus, '+9')
        self.char.characterattackmodifiers.refresh_from_db()
        self.assertEqual(self.char.characterattackmodifiers.GrapplerBBA, 6)

    def test_htmx_post_equipment_caps_dexterity_and_applies_armor_penalty_to_swim(self):
        swim = CharacterSkill.objects.get(Character=self.char, SkillName='Natacao')
        swim.Ranks = 2
        swim.MiscModifier = 1
        swim.save()
        self.char.characterstats.Strength = 16
        self.char.characterstats.Dexterity = 18
        self.char.characterstats.save()

        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'armor_Name': 'Chainmail',
                'armor_Type': 'Media',
                'armor_ACBonus': '+5',
                'armor_MaxDex': '+2',
                'armor_CheckPenalty': '-4',
                'armor_SpellFailure': '30%',
                'armor_Speed': '20 ft.',
                'armor_Weigth': '40 lb',
                'armor_SpecialProperties': '',
                'shield_Name': '',
                'shield_ACBonus': '',
                'shield_Weigth': '',
                'shield_CheckPenalty': '',
                'shield_SpellFailure': '',
                'shield_SpecialProperties': '',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterEquipmentForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.char.characterstatus.refresh_from_db()
        swim.refresh_from_db()
        self.assertEqual(self.char.characterstatus.ACDexModifier, 2)
        self.assertEqual(self.char.characterstatus.ACTotal, 17)
        self.assertEqual(swim.SkillModifier, -2)

    def test_htmx_post_status_speed_is_manual_and_persists_unreduced(self):
        # Deslocamento e 100% manual: o valor digitado persiste como base, sem
        # reducao automatica por carga sobrescrevendo a fonte.
        self.char.characterstats.Strength = 10
        self.char.characterstats.save()
        CharacterOtherItem.objects.create(Character=self.char, Name='Big chest', Weigth='120 lb')

        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {'Speed': '30'},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatusForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.char.characterstatus.refresh_from_db()
        self.assertEqual(self.char.characterstatus.Speed, 30)

    def test_recalculate_does_not_mutate_typed_speed(self):
        # Regressao: _recalculate_stats nao pode encolher o Speed a cada chamada
        # (antes: 30 -> 20 -> 15 -> 5 sob sobrecarga).
        from .views import _recalculate_stats
        self.char.characterstats.Strength = 10
        self.char.characterstats.save()
        CharacterOtherItem.objects.create(Character=self.char, Name='Big chest', Weigth='120 lb')
        self.char.characterstatus.Speed = 30
        self.char.characterstatus.save()

        for _ in range(3):
            _recalculate_stats(self.char)
            self.char.characterstatus.refresh_from_db()
            self.assertEqual(self.char.characterstatus.Speed, 30)

    def test_htmx_post_stats_persists_spell_save_dc_and_bonus_spells(self):
        self.char.Class = 'Wizard'
        self.char.Level = '1'
        self.char.save(update_fields=['Class', 'Level'])

        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'Strength': '10',
                'Dexterity': '10',
                'Constitution': '10',
                'Intelligence': '26',
                'Wisdom': '10',
                'Charisma': '10',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatsForm',
        )

        self.assertEqual(resp.status_code, 200)
        level_zero = CharacterMagicDayUse.objects.get(Character=self.char, Level=0)
        level_one = CharacterMagicDayUse.objects.get(Character=self.char, Level=1)
        self.assertEqual(level_zero.BonusSpells, 0)
        self.assertEqual(level_one.SpellSaveDC, 19)
        self.assertEqual(level_one.BonusSpells, 2)


class CharacterSheetWeaponLayoutTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Fighter')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})

    def test_character_sheet_renders_five_compact_attack_slots_with_ammo(self):
        CharacterWeapon.objects.create(
            Character=self.char,
            Attack='Longsword',
            AttackBonus='+4',
            Damage='1d8+2',
            Critical='19-20/x2',
            Range='-',
            Type='Slashing',
            Notes='Melee',
            AmmunitionName='Arrows',
        )
        CharacterWeapon.objects.create(Character=self.char, Name='Shortbow', AttackBonus='+3')

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'attack-card--compact', count=4)
        self.assertContains(resp, 'class="attack-ammo"', count=4)
        self.assertContains(resp, 'name="ammo_', count=120)
        self.assertContains(resp, 'Arrows')
        self.assertContains(resp, 'Longsword')
        self.assertContains(resp, 'Shortbow')
        self.assertContains(resp, 'weaponCard-empty-4')

    def test_character_sheet_splits_front_and_back_pages(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'sheet-page--front')
        self.assertContains(resp, 'sheet-page--back')
        self.assertContains(resp, 'sheet-page-break')
        self.assertContains(resp, 'sheet-lists-grid')


class HitPointTrackingTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user(username='hitpointuser')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='HitPoints')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})
        self.client.force_login(self.user)

    def test_status_post_allows_hit_points_above_max_and_floors_negatives(self):
        # PV atual e temporario PODEM exceder o maximo (cura excedente, PV
        # temporario, buffs). So ha piso 0; nao ha teto pelo TotalHitPoints.
        resp = self.client.post(
            self.url,
            {
                'TotalHitPoints': '24',
                'CurrentHitPoints': '99',
                'TemporaryHitPoints': '7',
                'NonLethalDamager': '-5',
                'Speed': '30',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatusForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.char.characterstatus.refresh_from_db()
        self.assertEqual(self.char.characterstatus.TotalHitPoints, 24)
        self.assertEqual(self.char.characterstatus.CurrentHitPoints, 99)
        self.assertEqual(self.char.characterstatus.TemporaryHitPoints, 7)
        self.assertEqual(self.char.characterstatus.NonLethalDamager, 0)

        page = self.client.get(self.url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'name="CurrentHitPoints"')
        self.assertContains(page, 'name="TemporaryHitPoints"')

    def test_back_page_renders_equipment_and_other_items_columns(self):
        CharacterArmor.objects.create(Character=self.char, Name='Chainmail', Type='Medium', ACBonus='+5')
        CharacterShield.objects.create(Character=self.char, Name='Heavy Shield', ACBonus='+2')
        CharacterProtectionItem.objects.create(Character=self.char, Name='Ring of Protection', ACBonus='+1')

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'EQUIPAMENTOS')
        self.assertContains(resp, 'Outros Itens')
        self.assertContains(resp, 'class="sheet-table other-items-table"', count=2)
        self.assertContains(resp, 'Chainmail')
        self.assertContains(resp, 'Heavy Shield')
        self.assertContains(resp, 'Ring of Protection')
        self.assertContains(resp, 'Item de Protecao', count=5)

    def test_pv_headers_render_above_fields_and_ac_labels_remain_below(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'class="pvca-headrow pv-headrow"')
        self.assertNotContains(resp, 'class="pvca-headrow ca-headrow"')
        self.assertContains(resp, '<span class="label">Armadura</span>', html=True)
        self.assertContains(resp, '<span class="label">Reducao de Dano</span>', html=True)


class CharacterAuxiliaryPageTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        setup_sdr_spell_table()
        self.user = make_user()
        self.other = make_user('mallory')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Auxiliar', Class='Druid', Level='7')
        _bootstrap_character_siblings(self.char)

    def test_character_sheet_links_auxiliary_pages(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('character:character', kwargs={'pk': self.char.pk}))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse('character:companions', kwargs={'pk': self.char.pk}))
        self.assertContains(resp, reverse('character:daily-resources', kwargs={'pk': self.char.pk}))
        self.assertContains(resp, reverse('character:reputation', kwargs={'pk': self.char.pk}))

    def test_companions_page_renders_animal_familiar_and_druid_summons(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('character:companions', kwargs={'pk': self.char.pk}))

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'character/companions.html')
        self.assertContains(resp, 'data-sheet-table="animal-companion"')
        self.assertContains(resp, 'data-sheet-table="familiar"')
        self.assertContains(resp, 'data-sheet-table="summon-nature-reference"')
        self.assertContains(resp, 'Aliado da Natureza IX')
        self.assertContains(resp, 'id="summonsGrid"')
        self.assertContains(resp, 'id="summon-search-input"')
        self.assertContains(resp, 'data-summon-card="empty"', count=3)

    def test_daily_resources_page_renders_trackers(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('character:daily-resources', kwargs={'pk': self.char.pk}))

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'character/daily_resources.html')
        self.assertContains(resp, 'data-sheet-table="daily-resource-tracker"')
        self.assertContains(resp, 'data-sheet-table="active-effects"')
        self.assertContains(resp, 'data-derived="dailyResource.Remaining"', count=18)
        self.assertContains(resp, 'data-field="activeEffect.Name"', count=12)

    def test_reputation_page_renders_contacts_factions_and_contracts(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('character:reputation', kwargs={'pk': self.char.pk}))

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'character/reputation.html')
        self.assertContains(resp, 'data-sheet-table="contacts"')
        self.assertContains(resp, 'data-sheet-table="factions"')
        self.assertContains(resp, 'data-sheet-table="contracts"')
        self.assertContains(resp, 'data-field="contact.Name"', count=16)
        self.assertContains(resp, 'data-field="contract.Title"', count=12)

    def test_auxiliary_pages_require_owner(self):
        for route_name in ['companions', 'daily-resources', 'reputation']:
            with self.subTest(route_name=route_name):
                url = reverse(f'character:{route_name}', kwargs={'pk': self.char.pk})

                resp = self.client.get(url)
                self.assertRedirects(resp, f"{reverse('login')}?next={url}", fetch_redirect_response=False)

                self.client.force_login(self.other)
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 404)
                self.client.logout()


class CompanionsTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Druid')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:companions', kwargs={'pk': self.char.pk})
        self.client.force_login(self.user)

    def test_htmx_post_creates_and_updates_companion_slots(self):
        resp_animal = self.client.post(
            self.url,
            {
                'animalCompanion_1_Name': 'Bruma',
                'animalCompanion_1_Species': 'Lobo',
                'animalCompanion_1_HitPoints': '24',
                'animalCompanion_1_ArmorClass': '16',
                'animalCompanion_1_Speed': '15 m',
                'animalCompanion_1_SpecialAbilities': 'Faro',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='animalCompanionsForm',
        )

        self.assertEqual(resp_animal.status_code, 200)
        self.assertTemplateUsed(resp_animal, 'character/partials/companions_animal_form.html')
        bruma = CharacterCompanion.objects.get(Character=self.char, Name='Bruma')
        self.assertEqual(bruma.Type, 'animal')
        self.assertEqual(bruma.Species, 'Lobo')
        self.assertEqual(bruma.HitPoints, 24)
        self.assertContains(resp_animal, 'Bruma')

        resp_familiar = self.client.post(
            self.url,
            {
                'familiar_1_Name': 'Nix',
                'familiar_1_Species': 'Coruja',
                'familiar_1_HitPoints': '8',
                'familiar_1_ArmorClass': '14',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='familiarsForm',
        )

        self.assertEqual(resp_familiar.status_code, 200)
        self.assertTemplateUsed(resp_familiar, 'character/partials/companions_familiar_form.html')
        nix = CharacterCompanion.objects.get(Character=self.char, Name='Nix')
        self.assertEqual(nix.Type, 'familiar')
        self.assertEqual(CharacterCompanion.objects.filter(Character=self.char).count(), 2)
        self.assertContains(resp_familiar, 'Nix')

    def test_get_reflects_saved_companion_data(self):
        CharacterCompanion.objects.create(
            Character=self.char,
            Type='Animal',
            Name='Bruma',
            Species='Lobo',
            HitPoints=24,
            ArmorClass=16,
            Speed='15 m',
        )

        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'animalCompanionsForm')
        self.assertContains(resp, 'Bruma')
        self.assertContains(resp, 'Lobo')

    def test_empty_slots_do_not_create_rows(self):
        resp = self.client.post(
            self.url,
            {'animalCompanion_1_Name': ''},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='animalCompanionsForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CharacterCompanion.objects.filter(Character=self.char).count(), 0)


class ReputationTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Face')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:reputation', kwargs={'pk': self.char.pk})
        self.client.force_login(self.user)

    def test_htmx_post_creates_contact_slots(self):
        resp = self.client.post(
            self.url,
            {
                'contact_1_Name': 'Mestre Ardan',
                'contact_1_Location': 'Greyhawk',
                'contact_1_Relationship': 'Aliado',
                'contact_1_Favor': '1',
                'contact_1_Notes': 'Sabe sobre portais',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='reputationContactsForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'character/partials/reputation_contacts_form.html')
        contact = CharacterContact.objects.get(Character=self.char)
        self.assertEqual(contact.Name, 'Mestre Ardan')
        self.assertEqual(contact.Location, 'Greyhawk')
        self.assertContains(resp, 'Mestre Ardan')

    def test_htmx_post_creates_faction_slots(self):
        resp = self.client.post(
            self.url,
            {
                'faction_1_Name': 'Circulo Esmeralda',
                'faction_1_Reputation': '+2',
                'faction_1_Influence': 'Regional',
                'faction_1_Risk': 'Baixo',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='reputationFactionsForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'character/partials/reputation_factions_form.html')
        faction = CharacterFaction.objects.get(Character=self.char)
        self.assertEqual(faction.Name, 'Circulo Esmeralda')
        self.assertEqual(faction.Reputation, '+2')

    def test_htmx_post_creates_contract_slots(self):
        resp = self.client.post(
            self.url,
            {
                'contract_1_Title': 'Recuperar o selo',
                'contract_1_Party': 'Lady Merin',
                'contract_1_Reward': '500 po',
                'contract_1_Deadline': 'Lua cheia',
                'contract_1_Status': 'Aberto',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='reputationContractsForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'character/partials/reputation_contracts_form.html')
        contract = CharacterContract.objects.get(Character=self.char)
        self.assertEqual(contract.Title, 'Recuperar o selo')
        self.assertEqual(contract.Status, 'Aberto')

    def test_get_reflects_saved_reputation_data(self):
        CharacterContact.objects.create(Character=self.char, Name='Mestre Ardan')
        CharacterFaction.objects.create(Character=self.char, Name='Circulo Esmeralda')
        CharacterContract.objects.create(Character=self.char, Title='Recuperar o selo')

        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'character/reputation.html')
        self.assertContains(resp, 'reputationContactsForm')
        self.assertContains(resp, 'Mestre Ardan')
        self.assertContains(resp, 'Circulo Esmeralda')
        self.assertContains(resp, 'Recuperar o selo')


class DailyResourcesDjangoIntegrationTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Recursos', Class='Druid', Level='7')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:daily-resources', kwargs={'pk': self.char.pk})

    def test_bootstrap_creates_daily_notes_singleton(self):
        from .models import CharacterDailyNotes
        self.assertTrue(CharacterDailyNotes.objects.filter(Character=self.char).exists())

    def test_daily_resource_remaining_is_derived(self):
        from .calculations import daily_resource_remaining
        self.assertEqual(daily_resource_remaining(5, 2), 3)
        self.assertEqual(daily_resource_remaining(2, 5), 0)

    def test_get_renders_saved_daily_resources_effects_and_notes(self):
        from .models import CharacterActiveEffect, CharacterDailyResource
        CharacterDailyResource.objects.create(
            Character=self.char,
            Name='Forma Selvagem',
            Source='Druida',
            Maximum=3,
            Used=1,
            Remaining=2,
            Refresh='Diario',
            Checks='1',
        )
        CharacterActiveEffect.objects.create(
            Character=self.char,
            Name='Pele de Arvore',
            Source='Magia',
            Modifier='+3 CA natural',
            RoundsRemaining=60,
            Notes='Ja aplicado',
        )
        self.char.characterdailynotes.Preparation = 'Preparar magias ao amanhecer'
        self.char.characterdailynotes.Spent = 'Forma selvagem usada uma vez'
        self.char.characterdailynotes.save()

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Forma Selvagem')
        self.assertContains(resp, 'Pele de Arvore')
        self.assertContains(resp, 'Preparar magias ao amanhecer')
        self.assertContains(resp, 'data-derived="dailyResource.Remaining"')
        self.assertContains(resp, '>2</div>', html=False)

    def test_htmx_post_daily_resources_saves_and_returns_page_fragment(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {
                'resource_1_Name': 'Forma Selvagem',
                'resource_1_Source': 'Druida',
                'resource_1_Maximum': '3',
                'resource_1_Used': '1',
                'resource_1_Refresh': 'Diario',
                'resource_1_Checks_1': 'on',
                'effect_1_Name': 'Pele de Arvore',
                'effect_1_Source': 'Magia',
                'effect_1_Modifier': '+3 CA natural',
                'effect_1_RoundsRemaining': '60',
                'effect_1_Notes': 'Ativo',
                'Preparation': 'Preparar magias',
                'Spent': 'Nada ainda',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='dailyResourcesForm',
        )

        self.assertEqual(resp.status_code, 200)
        from .models import CharacterActiveEffect, CharacterDailyResource
        resource = CharacterDailyResource.objects.get(Character=self.char)
        effect = CharacterActiveEffect.objects.get(Character=self.char)
        self.char.characterdailynotes.refresh_from_db()
        self.assertEqual(resource.Name, 'Forma Selvagem')
        self.assertEqual(resource.Remaining, 2)
        self.assertEqual(resource.Checks, '1')
        self.assertEqual(effect.Name, 'Pele de Arvore')
        self.assertEqual(self.char.characterdailynotes.Preparation, 'Preparar magias')
        self.assertContains(resp, 'dailyResourcesForm')
        self.assertContains(resp, 'Forma Selvagem')


class SpellcastingCalculationTests(TestCase):

    def test_spell_save_dc_uses_dnd_ability_modifier(self):
        from .spellcasting import spell_save_dc
        self.assertEqual(spell_save_dc(3, 18), 17)

    def test_bonus_spells_follow_ability_modifier_thresholds(self):
        from .spellcasting import bonus_spells_for_level
        self.assertEqual(bonus_spells_for_level(18, 1), 1)
        self.assertEqual(bonus_spells_for_level(18, 4), 1)
        self.assertEqual(bonus_spells_for_level(18, 5), 0)
        self.assertEqual(bonus_spells_for_level(18, 0), 0)


class CharacterCoreCalculationTests(TestCase):

    def test_skill_graduation_limits_follow_character_level(self):
        from .calculations import skill_graduation_limits
        self.assertEqual(skill_graduation_limits('5'), (8, 4))
        self.assertEqual(skill_graduation_limits('1'), (4, 2))
        self.assertEqual(skill_graduation_limits(''), (0, 0))

    def test_skill_total_uses_ability_ranks_and_misc(self):
        from .calculations import skill_total
        self.assertEqual(skill_total(3, 4, 2), 9)
        self.assertEqual(skill_total(-1, 0, 0), -1)
        self.assertEqual(skill_total(3, 0, 2, trained_only=True), 0)

    def test_skill_ability_modifier_uses_skill_name_mapping(self):
        from .calculations import skill_ability_modifier
        stats = {'Strength': 16, 'Dexterity': 14, 'Intelligence': 12, 'Wisdom': 8, 'Charisma': 10}
        self.assertEqual(skill_ability_modifier('Escalar', stats), 3)
        self.assertEqual(skill_ability_modifier('Esconder-se', stats), 2)
        self.assertEqual(skill_ability_modifier('Sobrevivencia', stats), -1)
        self.assertEqual(skill_ability_modifier('Unknown Skill', stats), 0)

    def test_load_limits_follow_strength_table(self):
        from .calculations import load_limits_for_strength
        self.assertEqual(load_limits_for_strength(10), (33, 66, 100, 100, 200, 500))
        self.assertEqual(load_limits_for_strength(16), (76, 153, 230, 230, 460, 1150))
        self.assertEqual(load_limits_for_strength(0), (0, 0, 0, 0, 0, 0))

    def test_total_carried_weight_parses_lbs_from_equipment_values(self):
        from .calculations import total_carried_weight
        self.assertEqual(total_carried_weight(['40 lb', '15 lb', '2.5 lb', '-', '', None]), 58)

    def test_parse_bonus_accepts_signed_equipment_text(self):
        from .calculations import parse_bonus
        self.assertEqual(parse_bonus('+5'), 5)
        self.assertEqual(parse_bonus('-2 penalidade'), -2)
        self.assertEqual(parse_bonus(''), 0)
        self.assertEqual(parse_bonus(None), 0)

    def test_equipment_armor_class_bonuses_sum_protection_items(self):
        from .calculations import equipment_armor_class_bonuses
        self.assertEqual(equipment_armor_class_bonuses('+5', '+2', ['+1', '2']), (5, 2, 3))


class CharacterProgressTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Progress', Level='5')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})

    def test_xp_to_next_level_uses_current_character_level(self):
        from .views import _xp_to_next_level
        self.assertEqual(_xp_to_next_level('5', 12000), 3000)
        self.assertEqual(_xp_to_next_level('5', 15000), 0)
        self.assertIsNone(_xp_to_next_level('', 0))

    def test_sheet_renders_progress_table_with_campaign_and_next_xp(self):
        self.char.characterprogress.CampaignName = 'A Fronteira'
        self.char.characterprogress.ExperiencePoints = 12000
        self.char.characterprogress.save()

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-sheet-table="campaign-progress"')
        self.assertContains(resp, 'A Fronteira')
        self.assertContains(resp, 'data-derived="XPToNextLevel"')
        self.assertContains(resp, '3000')

    def test_htmx_post_progress_saves_campaign_and_xp(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {'CampaignName': 'Mar Interior', 'ExperiencePoints': '14000'},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterProgressForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.char.characterprogress.refresh_from_db()
        self.assertEqual(self.char.characterprogress.CampaignName, 'Mar Interior')
        self.assertEqual(self.char.characterprogress.ExperiencePoints, 14000)
        self.assertContains(resp, 'characterProgressForm')
        self.assertContains(resp, '1000')


class CharacterSpellcastingRenderTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        setup_sdr_spell_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Caster', Class='Cleric', Level='1')
        _bootstrap_character_siblings(self.char)
        self.char.characterstats.Wisdom = 18
        self.char.characterstats.save()
        self.char.characterspellcasting.Domain1 = 'Healing'
        self.char.characterspellcasting.Domain2 = ''
        self.char.characterspellcasting.save()
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})
        self.spellbook_url = reverse('character:spellbook', kwargs={'pk': self.char.pk})

    def test_cleric_sheet_renders_domain_and_daily_spell_summary(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'MAGIAS')
        self.assertContains(resp, 'Dominio Healing')
        self.assertContains(resp, 'Restam')
        self.assertContains(resp, 'Abrir Livro de Magias')

    def test_htmx_toggle_spell_slot_marks_used_and_returns_spells_partial(self):
        slot = CharacterSpellSlot.objects.create(
            Character=self.char,
            Level=1,
            SlotType='normal',
            PreparedSpellName='bless',
            IsUsed=False,
        )
        self.client.force_login(self.user)

        resp = self.client.post(
            reverse('character:toggle-spell-slot', kwargs={'pk': self.char.pk, 'slot_id': slot.pk}),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(resp.status_code, 200)
        slot.refresh_from_db()
        self.assertTrue(slot.IsUsed)
        self.assertContains(resp, 'spellbookSlotsForm')
        self.assertContains(resp, 'bless')
        follow_up = self.client.get(self.spellbook_url)
        self.assertContains(follow_up, 'bless')
        self.assertContains(follow_up, 'is-used')

    def test_spell_slot_toggle_markup_posts_to_slot_partial(self):
        slot = CharacterSpellSlot.objects.create(
            Character=self.char,
            Level=1,
            SlotType='normal',
            PreparedSpellName='shield',
            IsUsed=False,
        )

        self.client.force_login(self.user)
        resp = self.client.get(self.spellbook_url)

        self.assertContains(resp, 'spell-used-toggle')
        self.assertContains(resp, 'type="button"')
        self.assertContains(
            resp,
            reverse('character:toggle-spell-slot', kwargs={'pk': self.char.pk, 'slot_id': slot.pk}),
        )
        self.assertContains(resp, 'hx-target="#spellbookSlotsForm"')

    def test_sorcerer_sheet_renders_known_spells_mode(self):
        self.char.Class = 'Sorcerer'
        self.char.save()
        self.char.characterstats.Charisma = 16
        self.char.characterstats.save()
        CharacterSpell.objects.create(Character=self.char, Name='magic missile', Level=1, Page='251')

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertContains(resp, 'spontaneous_known')
        self.assertContains(resp, 'CAR')

    def test_wizard_sheet_renders_specialized_school(self):
        self.char.Class = 'Wizard'
        self.char.save()
        self.char.characterstats.Intelligence = 17
        self.char.characterstats.save()
        self.char.characterspellcasting.SpecializedSchool = 'Evocation'
        self.char.characterspellcasting.save()

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertContains(resp, 'prepared_book')
        self.assertContains(resp, 'Evocation')
        self.assertContains(resp, 'INT')

    def test_any_class_can_render_custom_spellcasting(self):
        self.char.Class = 'Fighter'
        self.char.save()

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertContains(resp, 'MAGIAS')
        self.assertContains(resp, 'Abrir Livro de Magias')
        self.assertContains(resp, 'data-sheet-table="spellcasting-summary"')


class SpellbookPageTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        setup_sdr_spell_table()
        from .seeds import seed_admin, seed_wizard
        self.char = seed_wizard(seed_admin())
        self.user = self.char.User
        self.url = reverse('character:spellbook', kwargs={'pk': self.char.pk})
        self.client.force_login(self.user)

    def test_spellbook_groups_maelis_vorn_spells_by_level(self):
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'character/spellbook.html')
        self.assertContains(resp, 'Maelis Vorn')
        self.assertContains(resp, 'Livro de Magias')
        self.assertContains(resp, 'spellbookSlotsForm')
        self.assertContains(resp, 'Slots por nivel')
        self.assertContains(resp, 'spellbookLevel0Form')
        self.assertContains(resp, 'spellbookLevel4Form')
        self.assertContains(resp, 'Detectar Magia')
        self.assertContains(resp, 'Mísseis Mágicos')
        self.assertContains(resp, 'Bola de Fogo')

    def test_htmx_post_updates_spellbook_section(self):
        level_one_spells = list(CharacterSpell.objects.filter(Character=self.char, Level=1).order_by('id'))
        payload = {}
        for index, spell in enumerate(level_one_spells, start=1):
            payload[f'spellbook_1_{index}_Name'] = spell.Name
            payload[f'spellbook_1_{index}_Page'] = spell.Page
        payload['spellbook_1_1_Page'] = 'PHB-2'

        resp = self.client.post(
            self.url,
            payload,
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='spellbookLevel1Form',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'character/partials/spellbook_level_form.html')
        updated = CharacterSpell.objects.get(Character=self.char, Level=1, Name=level_one_spells[0].Name)
        self.assertEqual(updated.Page, 'PHB-2')

    def test_spellbook_casting_mode_renders_as_select_with_all_options(self):
        resp = self.client.get(self.url)

        self.assertContains(resp, 'name="spellcasting_CastingMode"')
        self.assertContains(resp, '<option value="prepared_book"')
        self.assertContains(resp, '<option value="spontaneous_known"')
        self.assertContains(resp, '<option value="prepared_divine"')
        self.assertContains(resp, '<option value="custom"')
        # Wizard seed defaults to prepared_book
        self.assertContains(resp, 'value="prepared_book" selected')

    def test_spellbook_does_not_duplicate_summary_table(self):
        resp = self.client.get(self.url)

        self.assertNotContains(resp, 'data-sheet-table="spellcasting-summary"')
        self.assertNotContains(resp, 'CD Resist.')

    def test_spellbook_renders_per_level_slot_cards_with_capacity(self):
        resp = self.client.get(self.url)

        self.assertContains(resp, 'spellbook-slot-grid')
        self.assertContains(resp, 'spellbook-slot-card')
        self.assertContains(resp, 'Nivel 1')
        # Wizard nv 8 INT 18 -> level 1 capacity should be at least 4 (4 per day + bonus)
        self.assertContains(resp, 'Restam')

    def test_spellbook_slot_toggle_uses_compact_visible_label(self):
        resp = self.client.get(self.url)

        self.assertContains(resp, 'class="spell-used-toggle btn-slot-cast')
        self.assertContains(resp, '<span class="btn-slot-cast-label">Gasta</span>', html=True)
        self.assertContains(resp, 'aria-label="Marcar como usada - ')
        self.assertNotContains(resp, '>Marcar como usada</button>')

    def test_spellbook_slot_post_persists_prepared_spell_name(self):
        payload = {
            'slot_1_Level': '1',
            'slot_1_SlotType': 'normal',
            'slot_1_PreparedSpellName': 'Escudo Arcano',
            'slot_1_ConvertedTo': '',
        }
        resp = self.client.post(
            self.url,
            payload,
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='spellbookSlotsForm',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            CharacterSpellSlot.objects.filter(
                Character=self.char,
                PreparedSpellName='Escudo Arcano',
            ).exists()
        )


class CharacterSpellsLeanTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        from .seeds import seed_admin, seed_wizard
        self.char = seed_wizard(seed_admin())
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})
        self.client.force_login(self.char.User)

    def test_character_spells_partial_is_lean(self):
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-sheet-table="spellcasting-summary"')
        self.assertContains(resp, 'Abrir Livro de Magias')
        self.assertNotContains(resp, 'data-sheet-table="prepared-spell-slots"')
        self.assertNotContains(resp, 'data-sheet-table="known-spells"')
        self.assertNotContains(resp, 'Slots Preparados / Usados')
        self.assertNotContains(resp, 'Magias Conhecidas / Grimorio')


class QueryCountTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Query', Class='Cleric', Level='1')
        _bootstrap_character_siblings(self.char)
        CharacterWeapon.objects.create(Character=self.char, Attack='Longsword')
        CharacterProtectionItem.objects.create(Character=self.char, Name='Ring', ACBonus='+1')
        CharacterOtherItem.objects.create(Character=self.char, Name='Rope')
        CharacterFeat.objects.create(Character=self.char, Name='Power Attack')
        CharacterSpellSlot.objects.create(Character=self.char, Level=1, PreparedSpellName='bless')
        CharacterSpell.objects.create(Character=self.char, Name='cure light wounds', Level=1)
        self.client.force_login(self.user)

    def test_character_sheet_render_keeps_default_query_count_bounded(self):
        with CaptureQueriesContext(connections['default']) as queries:
            resp = self.client.get(reverse('character:character', kwargs={'pk': self.char.pk}))

        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(queries), 16)

    def test_home_render_keeps_character_card_query_count_bounded(self):
        second = Character.objects.create(User=self.user, Name='Second')
        from .services import _bootstrap_character_siblings
        _bootstrap_character_siblings(second)

        with CaptureQueriesContext(connections['default']) as queries:
            resp = self.client.get(reverse('character:home'))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Query')
        self.assertContains(resp, 'Second')
        self.assertLessEqual(len(queries), 5)


class DispatcherSmokeTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Dispatcher', Class='Fighter', Level='1')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})
        self.client.force_login(self.user)

    def test_all_character_dispatcher_targets_return_expected_partials(self):
        cases = [
            ('characterIdentityForm', {
                'Name': 'Dispatcher', 'Class': 'Fighter', 'Level': '1',
                'Race': '', 'Alignment': '', 'Deity': '', 'Size': '',
                'Age': '', 'Sex': '', 'Heigth': '', 'Weight': '',
                'Eye': '', 'Hair': '', 'Skin': '',
            }, 'character/partials/character_identity.html'),
            ('characterForm', {'Description': 'Updated'}, 'character/partials/character_description.html'),
            ('characterStatsForm', {'Strength': '12'}, 'character/partials/character_attrs_form.html'),
            ('characterStatusForm', {'Speed': '9'}, 'character/partials/character_status_form.html'),
            ('characterArmorForm', {'ACSizeModifier': '0'}, 'character/partials/character_armor_form.html'),
            ('characterSavesForm', {'FortitudeBaseSave': '2'}, 'character/partials/character_saves_form.html'),
            ('characterAttackForm', {'BBA': '1'}, 'character/partials/character_attack_form.html'),
            ('characterSkillsForm', {'skill_1_Ranks': '1'}, 'character/partials/character_skills.html'),
            ('characterWeaponsForm', {'weapon_1_Attack': 'Longsword'}, 'character/partials/character_weapon_card.html'),
            ('characterProgressForm', {'ExperiencePoints': '1000'}, 'character/partials/character_progress.html'),
            ('characterEquipmentForm', {'armor_Name': 'Chain Shirt'}, 'character/partials/character_armor.html'),
            ('characterItemsForm', {'item_1_Name': 'Rope'}, 'character/partials/character_items.html'),
            ('characterMoneyForm', {'GP': '25'}, 'character/partials/character_money.html'),
            ('characterFeatsForm', {'feat_1_Name': 'Power Attack'}, 'character/partials/character_feats.html'),
            ('characterSpecialsForm', {'ability_1_Name': 'Darkvision'}, 'character/partials/character_specials.html'),
            ('characterSpellsForm', {'known_spell_1_Name': 'Bless'}, 'character/partials/character_spells.html'),
        ]

        for target, payload, template in cases:
            with self.subTest(target=target):
                resp = self.client.post(
                    self.url,
                    payload,
                    HTTP_HX_REQUEST='true',
                    HTTP_HX_TARGET=target,
                )

                self.assertEqual(resp.status_code, 200)
                self.assertTemplateUsed(resp, template)


class EndToEndSmoke(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()

    def test_user_creates_character_edits_strength_and_sees_recalculated_modifier(self):
        User.objects.create_user(username='e2e', password='pass')
        login_resp = self.client.post(reverse('login'), {'username': 'e2e', 'password': 'pass'})
        self.assertEqual(login_resp.status_code, 302)

        create_resp = self.client.post(
            reverse('character:create-character'),
            {'Name': 'Smoke', 'Description': 'Fluxo ponta a ponta'},
        )
        char = Character.objects.get(Name='Smoke')
        self.assertRedirects(
            create_resp,
            reverse('character:character', kwargs={'pk': char.pk}),
            fetch_redirect_response=False,
        )

        edit_resp = self.client.post(
            reverse('character:character', kwargs={'pk': char.pk}),
            {'Strength': '16'},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatsForm',
        )
        self.assertEqual(edit_resp.status_code, 200)
        self.assertTemplateUsed(edit_resp, 'character/partials/character_attrs_form.html')

        char.characterstats.refresh_from_db()
        self.assertEqual(char.characterstats.Strength, 16)
        self.assertEqual(char.characterstats.StrengthStatMod, 3)

        get_resp = self.client.get(reverse('character:character', kwargs={'pk': char.pk}))
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'data-derived="StrengthStatMod">3')


class SDRClassChoicesTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()

    def test_sdr_class_choices_has_phb_core(self):
        from .services import sdr_class_choices
        codes = {c for c, _ in sdr_class_choices()}
        for cls in ['Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter',
                    'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer', 'Wizard']:
            self.assertIn(cls, codes, f"SDR não retornou {cls} — provavelmente esqueceu .using('sdr')")


class SDRClassFilteringTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()

    def test_sdr_class_choices_excludes_non_phb_base_classes_and_uses_portuguese_labels(self):
        SDR_Class.objects.using('sdr').create(name='Assassin')
        SDR_Class.objects.using('sdr').create(name='Loremaster')

        from .services import sdr_class_choices
        choices = sdr_class_choices()
        codes = [code for code, _label in choices]
        labels = dict(choices)

        self.assertNotIn('Assassin', codes)
        self.assertNotIn('Loremaster', codes)
        self.assertEqual(labels['Fighter'], 'Guerreiro')
        self.assertEqual(labels['Wizard'], 'Mago')
        self.assertEqual(len([code for code in codes if code]), 11)


class ReferenceDataTests(TestCase):

    def test_alignment_choices_are_two_letter_codes(self):
        from .constants import ALIGNMENT_CHOICES
        codes = [c for c, _ in ALIGNMENT_CHOICES if c]
        self.assertEqual(set(codes), {'LG', 'NG', 'CG', 'LN', 'N', 'CN', 'LE', 'NE', 'CE'})

    def test_size_choices_have_nine_categories(self):
        from .constants import SIZE_CHOICES
        codes = {c for c, _ in SIZE_CHOICES if c}
        self.assertEqual(codes, {'F', 'D', 'T', 'S', 'M', 'L', 'H', 'G', 'C'})

    def test_race_choices_count(self):
        from .constants import RACE_CHOICES
        # 7 raças + entrada vazia
        self.assertEqual(len(RACE_CHOICES), 8)

    def test_deity_suggestions_count(self):
        from .constants import DEITY_SUGGESTIONS
        self.assertEqual(len(DEITY_SUGGESTIONS), 19)


class AlignmentValidationTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='T')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})

    def test_invalid_alignment_returns_form_error(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            self.url,
            {'Name': 'T', 'Alignment': 'XX', 'Class': '', 'Level': '',
             'Race': '', 'Size': '', 'Deity': '', 'Age': '', 'Sex': '',
             'Heigth': '', 'Weight': '', 'Eye': '', 'Hair': '', 'Skin': ''},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterIdentityForm',
        )
        # form invalid → still returns partial with errors, not 200 saving
        self.char.refresh_from_db()
        self.assertNotEqual(self.char.Alignment, 'XX')


class FieldValidationTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Validation')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})
        self.client.force_login(self.user)

    def test_integer_fields_are_clamped_without_500(self):
        resp = self.client.post(
            self.url,
            {'Speed': '5000'},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatusForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.char.characterstatus.refresh_from_db()
        self.assertEqual(self.char.characterstatus.Speed, 999)

    def test_repeating_slot_strings_are_stripped_and_truncated_to_max_length(self):
        long_attack = f"  {'x' * 250}  "
        resp = self.client.post(
            self.url,
            {'weapon_1_Attack': long_attack},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterWeaponsForm',
        )

        self.assertEqual(resp.status_code, 200)
        weapon = CharacterWeapon.objects.get(Character=self.char)
        self.assertEqual(weapon.Attack, 'x' * 200)

    def test_repeating_slot_integer_fields_are_clamped(self):
        resp = self.client.post(
            self.url,
            {
                'known_spell_1_Name': 'Raio Arcano',
                'known_spell_1_Level': '-5000',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterSpellsForm',
        )

        self.assertEqual(resp.status_code, 200)
        spell = CharacterSpell.objects.get(Character=self.char, Name='Raio Arcano')
        self.assertEqual(spell.Level, -999)

    def test_html_text_is_preserved_as_plain_database_value(self):
        payload = '  <script>alert(1)</script>  '
        resp = self.client.post(
            self.url,
            {'feat_1_Name': payload},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterFeatsForm',
        )

        self.assertEqual(resp.status_code, 200)
        feat = CharacterFeat.objects.get(Character=self.char)
        self.assertEqual(feat.Name, '<script>alert(1)</script>')


# ---------------------------------------------------------------------------
# Phase A — home redirect and character list filtering
# ---------------------------------------------------------------------------

class HomeRedirectTests(TestCase):

    def test_anonymous_gets_landing(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'home/landing.html')
        self.assertContains(resp, 'Entrar')
        self.assertContains(resp, 'character_sheet')

    def test_authenticated_redirects_to_character_home(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.get('/')
        self.assertRedirects(resp, reverse('character:home'), fetch_redirect_response=False)


class CharacterHomeLoginRequiredTests(TestCase):

    def test_anonymous_redirects_to_login(self):
        resp = self.client.get(reverse('character:home'))
        self.assertRedirects(
            resp,
            f"{reverse('login')}?next={reverse('character:home')}",
            fetch_redirect_response=False,
        )

    def test_authenticated_sees_only_own_characters(self):
        alice = make_user('alice')
        bob = make_user('bob')
        from .services import _bootstrap_character_siblings
        char_alice = Character.objects.create(User=alice, Name='Lancelot')
        _bootstrap_character_siblings(char_alice)
        char_bob = Character.objects.create(User=bob, Name='Mordred')
        _bootstrap_character_siblings(char_bob)

        self.client.force_login(alice)
        resp = self.client.get(reverse('character:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Lancelot')
        self.assertNotContains(resp, 'Mordred')


# ---------------------------------------------------------------------------
# Seeds — conta admin + fichas de exemplo usadas pelos testes
# ---------------------------------------------------------------------------

class SeedTests(TestCase):

    def test_seed_admin_creates_superuser_with_known_password(self):
        from .seeds import seed_admin, ADMIN_USERNAME, ADMIN_PASSWORD
        user = seed_admin()
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password(ADMIN_PASSWORD))
        # axes.AxesStandaloneBackend requires an HTTP request; use force_login to
        # verify the session mechanism works without going through authenticate().
        self.client.force_login(user)
        self.assertIn('_auth_user_id', self.client.session)

    def test_seed_admin_is_idempotent(self):
        from .seeds import seed_admin, ADMIN_USERNAME, ADMIN_PASSWORD
        first = seed_admin()
        second = seed_admin()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(User.objects.filter(username=ADMIN_USERNAME).count(), 1)
        self.assertTrue(second.check_password(ADMIN_PASSWORD))

    def test_seed_fighter_is_complete(self):
        from .seeds import seed_admin, seed_fighter
        char = seed_fighter(seed_admin())
        self.assertEqual(char.Class, 'Fighter')
        self.assertEqual(char.Level, '5')
        self.assertTrue(CharacterStats.objects.filter(Character=char).exists())
        self.assertTrue(CharacterStatus.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSavingThrows.objects.filter(Character=char).exists())
        self.assertEqual(CharacterSkill.objects.filter(Character=char).count(), 41)
        self.assertTrue(CharacterWeapon.objects.filter(Character=char).exists())
        self.assertTrue(CharacterArmor.objects.filter(Character=char).exists())
        self.assertTrue(CharacterShield.objects.filter(Character=char).exists())
        self.assertTrue(CharacterFeat.objects.filter(Character=char).exists())

    def test_seed_fighter_derived_values_are_consistent(self):
        from .seeds import seed_admin, seed_fighter
        char = seed_fighter(seed_admin())
        stats = char.characterstats
        status = char.characterstatus
        saves = char.charactersavingthrows
        attack = char.characterattackmodifiers

        self.assertEqual(stats.StrengthStatMod, (stats.Strength - 10) // 2)
        self.assertEqual(status.ACDexModifier, stats.DexterityStatMod)
        self.assertEqual(
            status.ACTotal,
            10 + status.ACArmorBonus + status.ACShieldBonus + status.ACDexModifier
            + status.ACSizeModifier + status.ACNaturalArmor
            + status.ACDeflectionModifier + status.ACMiscModifier,
        )
        self.assertEqual(
            saves.TotalFortitude,
            saves.FortitudeBaseSave + saves.FortitudeAbilityModifier
            + saves.FortitudeMagicModifier + saves.FortitudeMiscModifier
            + saves.FortitudeTemporaryModifier,
        )
        self.assertEqual(
            attack.TotalGrappler,
            attack.GrapplerBBA + attack.GrapplerStrModifier
            + attack.GrapplerSizeModifier + attack.GrapplerMiscModifier,
        )

    def test_seed_wizard_has_spellcasting_spellbook_and_slots(self):
        from .seeds import seed_admin, seed_wizard
        char = seed_wizard(seed_admin())
        self.assertEqual(char.Class, 'Wizard')
        self.assertEqual(char.Level, '8')
        sc = char.characterspellcasting
        self.assertEqual(sc.CasterClass, 'Wizard')
        self.assertEqual(sc.CastingMode, 'prepared_book')
        self.assertEqual(sc.SpecializedSchool, 'Evocation')
        self.assertTrue(CharacterSpellSlot.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSpell.objects.filter(Character=char).exists())
        self.assertEqual(
            char.characterstats.IntelligenceStatMod,
            (char.characterstats.Intelligence - 10) // 2,
        )

    def test_seed_druid_uses_summons_resources_buffs_and_reputation(self):
        from .seeds import seed_admin, seed_druid
        char = seed_druid(seed_admin())
        self.assertEqual(char.Class, 'Druid')
        self.assertEqual(char.Level, '9')
        self.assertTrue(CharacterCompanion.objects.filter(Character=char, Type='animal').exists())
        self.assertTrue(CharacterSummon.objects.filter(Character=char, Name__icontains='Urso').exists())
        self.assertTrue(CharacterDailyResource.objects.filter(Character=char).exists())
        self.assertTrue(CharacterActiveEffect.objects.filter(Character=char).exists())
        self.assertTrue(CharacterBuff.objects.filter(Character=char).exists())
        self.assertTrue(CharacterContact.objects.filter(Character=char).exists())
        self.assertTrue(CharacterFaction.objects.filter(Character=char).exists())
        self.assertTrue(CharacterContract.objects.filter(Character=char).exists())
        self.assertEqual(char.characterspellcasting.CasterClass, 'Druid')
        self.assertEqual(char.characterspellcasting.CastingMode, 'prepared_spontaneous')

    def test_seed_ranger_has_animal_companion_and_full_sheet_sections(self):
        from .seeds import seed_admin, seed_ranger
        char = seed_ranger(seed_admin())
        self.assertEqual(char.Class, 'Ranger')
        self.assertEqual(char.Level, '6')
        companion = CharacterCompanion.objects.get(Character=char, Type='animal')
        self.assertTrue(companion.Name)
        self.assertTrue(companion.Skills)
        self.assertTrue(CharacterDailyResource.objects.filter(Character=char).exists())
        self.assertTrue(CharacterContact.objects.filter(Character=char).exists())
        self.assertTrue(CharacterFaction.objects.filter(Character=char).exists())
        self.assertTrue(CharacterContract.objects.filter(Character=char).exists())
        self.assertGreaterEqual(CharacterWeapon.objects.filter(Character=char).count(), 2)

    def test_seed_all_is_idempotent_and_owned_by_admin(self):
        from .seeds import (
            seed_all, seed_admin, FIGHTER_NAME, WIZARD_NAME,
            DRUID_NAME, RANGER_NAME,
        )
        first = seed_all()
        second = seed_all()
        admin = seed_admin()
        self.assertEqual(Character.objects.filter(Name=FIGHTER_NAME).count(), 1)
        self.assertEqual(Character.objects.filter(Name=WIZARD_NAME).count(), 1)
        self.assertEqual(Character.objects.filter(Name=DRUID_NAME).count(), 1)
        self.assertEqual(Character.objects.filter(Name=RANGER_NAME).count(), 1)
        self.assertEqual(second['fighter'].User, admin)
        self.assertEqual(second['wizard'].User, admin)
        self.assertEqual(second['druid'].User, admin)
        self.assertEqual(second['ranger'].User, admin)
        # ids estáveis entre execuções (URLs /character/<id> não mudam)
        self.assertEqual(first['fighter'].pk, second['fighter'].pk)
        self.assertEqual(first['wizard'].pk, second['wizard'].pk)
        self.assertEqual(first['druid'].pk, second['druid'].pk)
        self.assertEqual(first['ranger'].pk, second['ranger'].pk)
        # rodar de novo não duplica filhos
        self.assertEqual(CharacterSkill.objects.filter(Character=second['fighter']).count(), 41)
        from sprites.models import SpriteAsset
        self.assertTrue(SpriteAsset.objects.filter(Slug='human_fighter_sword_shield').exists())


# ---------------------------------------------------------------------------
# T1.2 — Auth hardening: seed guard + django-axes brute force
# ---------------------------------------------------------------------------

class SeedAdminGuardTest(TestCase):

    def test_seed_all_raises_in_production_without_seed_admin_flag(self):
        """seed_all() sem DEBUG=true e sem SEED_ADMIN não cria admin em produção."""
        import os
        from unittest.mock import patch
        from character.seeds import seed_all
        with patch.dict(os.environ, {'DEBUG': '', 'SEED_ADMIN': ''}, clear=False):
            with self.assertRaises(RuntimeError):
                seed_all()

    def test_seed_all_creates_admin_when_debug_env_is_true(self):
        import os
        from unittest.mock import patch
        from character.seeds import seed_all, ADMIN_USERNAME
        with patch.dict(os.environ, {'DEBUG': 'True'}, clear=False):
            result = seed_all()
        self.assertIsNotNone(result['admin'])
        self.assertTrue(User.objects.filter(username=ADMIN_USERNAME).exists())


class LoginBruteForceTest(TestCase):

    def setUp(self):
        make_user('brutetest', 'CorrectP@ssword123!')
        self.login_url = reverse('login')

    def test_repeated_failed_logins_trigger_lockout(self):
        # 4 falhas → ainda não bloqueado
        for i in range(4):
            resp = self.client.post(
                self.login_url,
                {'username': 'brutetest', 'password': 'wrongpassword'},
                REMOTE_ADDR='192.0.2.1',
            )
            self.assertNotIn(resp.status_code, [403, 429], f"Bloqueado cedo demais na tentativa {i + 1}")

        # 5ª falha (AXES_FAILURE_LIMIT=5) → bloqueado
        resp = self.client.post(
            self.login_url,
            {'username': 'brutetest', 'password': 'wrongpassword'},
            REMOTE_ADDR='192.0.2.1',
        )
        self.assertIn(resp.status_code, [403, 429])


# ---------------------------------------------------------------------------
# T1.7 — Pure calculation functions in calculations.py
# ---------------------------------------------------------------------------

class PureCalculationsTest(TestCase):

    def test_compute_armor_class_base(self):
        from .calculations import compute_armor_class
        total, touch, flat = compute_armor_class(
            armor_bonus=5, shield_bonus=2, dex_mod=2, size_mod=0,
            natural_armor=0, deflection=1, misc=0,
        )
        self.assertEqual(total, 20)
        self.assertEqual(touch, 13)
        self.assertEqual(flat, 18)

    def test_compute_armor_class_zeros(self):
        from .calculations import compute_armor_class
        total, touch, flat = compute_armor_class(
            armor_bonus=0, shield_bonus=0, dex_mod=0, size_mod=0,
            natural_armor=0, deflection=0, misc=0,
        )
        self.assertEqual(total, 10)
        self.assertEqual(touch, 10)
        self.assertEqual(flat, 10)

    def test_compute_armor_class_negative_dex(self):
        from .calculations import compute_armor_class
        total, touch, flat = compute_armor_class(
            armor_bonus=4, shield_bonus=0, dex_mod=-2, size_mod=0,
            natural_armor=2, deflection=0, misc=0,
        )
        self.assertEqual(total, 14)
        self.assertEqual(touch, 8)
        self.assertEqual(flat, 16)

    def test_compute_save_total_sums_all_components(self):
        from .calculations import compute_save_total
        self.assertEqual(compute_save_total(base=3, ability_mod=2, magic=1, misc=0, temporary=0), 6)
        self.assertEqual(compute_save_total(base=0, ability_mod=-1, magic=0, misc=0, temporary=0), -1)
        self.assertEqual(compute_save_total(base=5, ability_mod=3, magic=2, misc=1, temporary=1), 12)

    def test_compute_grapple_total_sums_components(self):
        from .calculations import compute_grapple_total
        self.assertEqual(compute_grapple_total(bba=5, str_mod=3, size_mod=0, misc=0), 8)
        self.assertEqual(compute_grapple_total(bba=0, str_mod=0, size_mod=0, misc=0), 0)
        self.assertEqual(compute_grapple_total(bba=3, str_mod=-1, size_mod=-1, misc=2), 3)

    def test_compute_skill_row_returns_ability_key_and_modifier(self):
        from .calculations import compute_skill_row
        stats = {'Strength': 16, 'Dexterity': 14, 'Intelligence': 10}
        key, mod = compute_skill_row(skill_name='Escalar', stats=stats)
        self.assertEqual(key, 'FOR')
        self.assertEqual(mod, 3)

    def test_compute_skill_row_unknown_skill_returns_empty_key(self):
        from .calculations import compute_skill_row
        stats = {'Strength': 10}
        key, mod = compute_skill_row(skill_name='UnknownSkill', stats=stats)
        self.assertEqual(key, '')
        self.assertEqual(mod, 0)


class DerivedFieldCalculationsTest(SimpleTestCase):

    def test_compute_attack_bonus_sums_components(self):
        from .calculations import compute_attack_bonus
        self.assertEqual(compute_attack_bonus(bba=6, ability_mod=3, size_mod=-1, misc=0), 8)
        self.assertEqual(compute_attack_bonus(bba=0, ability_mod=0, size_mod=0, misc=0), 0)
        self.assertEqual(compute_attack_bonus(bba=3, ability_mod=-1, size_mod=1, misc=2), 5)

    def test_cap_dex_to_armor_uses_lowest_limit_and_allows_missing_cap(self):
        from .calculations import cap_dex_to_armor
        self.assertEqual(cap_dex_to_armor(4, None), 4)
        self.assertEqual(cap_dex_to_armor(4, ''), 4)
        self.assertEqual(cap_dex_to_armor(4, 2), 2)
        self.assertEqual(cap_dex_to_armor(-1, 0), -1)

    def test_armor_check_penalty_for_skill_only_hits_affected_skills(self):
        from .calculations import armor_check_penalty_for_skill
        self.assertEqual(armor_check_penalty_for_skill('Escalar', -4), -4)
        self.assertEqual(armor_check_penalty_for_skill('Equilibrio', -4), -4)
        self.assertEqual(armor_check_penalty_for_skill('Natacao', -4), -8)
        self.assertEqual(armor_check_penalty_for_skill('Concentracao', -4), 0)

    def test_speed_for_load_uses_standard_35_reductions(self):
        from .calculations import speed_for_load
        self.assertEqual(speed_for_load(base_speed=30, load_category='light', armor_speed=None), 30)
        self.assertEqual(speed_for_load(base_speed=30, load_category='heavy', armor_speed=None), 20)
        self.assertEqual(speed_for_load(base_speed=20, load_category='heavy', armor_speed=None), 15)
        self.assertEqual(speed_for_load(base_speed=30, load_category='light', armor_speed='20 ft.'), 20)

    def test_compute_spell_save_dc_uses_spell_level_and_ability_mod(self):
        from .calculations import compute_spell_save_dc
        self.assertEqual(compute_spell_save_dc(spell_level=0, casting_ability_mod=0), 10)
        self.assertEqual(compute_spell_save_dc(spell_level=3, casting_ability_mod=4), 17)
        self.assertEqual(compute_spell_save_dc(spell_level=6, casting_ability_mod=-1), 15)

    def test_bonus_spells_for_ability_matches_35_progression(self):
        from .calculations import bonus_spells_for_ability
        self.assertEqual(bonus_spells_for_ability(ability_score=10, spell_level=1), 0)
        self.assertEqual(bonus_spells_for_ability(ability_score=18, spell_level=1), 1)
        self.assertEqual(bonus_spells_for_ability(ability_score=26, spell_level=1), 2)
        self.assertEqual(bonus_spells_for_ability(ability_score=26, spell_level=5), 1)
        self.assertEqual(bonus_spells_for_ability(ability_score=26, spell_level=0), 0)


# ---------------------------------------------------------------------------
# T1.6 — _recalculate_stats: atomic + bulk_update
# ---------------------------------------------------------------------------

class RecalculateQueryBudget(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='QueryBudget', Level='5')
        _bootstrap_character_siblings(self.char)

    def test_recalculate_stats_stays_within_query_budget(self):
        from .views import _recalculate_stats
        # Refresh so relations are resolved before entering the measured block
        self.char.refresh_from_db()
        with CaptureQueriesContext(connections['default']) as ctx:
            _recalculate_stats(self.char)
        self.assertLessEqual(
            len(ctx.captured_queries), 23,
            f"_recalculate_stats usou {len(ctx.captured_queries)} queries (budget: 23)"
        )


# ---------------------------------------------------------------------------
# T1.4 — WhiteNoise + STATIC_ROOT
# ---------------------------------------------------------------------------

class StaticFilesTest(TestCase):

    def test_whitenoise_middleware_in_middleware(self):
        self.assertIn('whitenoise.middleware.WhiteNoiseMiddleware', settings.MIDDLEWARE)

    def test_static_root_configured_inside_base_dir(self):
        self.assertTrue(hasattr(settings, 'STATIC_ROOT'))
        self.assertTrue(str(settings.STATIC_ROOT).startswith(str(settings.BASE_DIR)))

    def test_whitenoise_storage_backend_configured(self):
        backend = settings.STORAGES['staticfiles']['BACKEND']
        self.assertIn('whitenoise', backend)


# ---------------------------------------------------------------------------
# T1.1 — Settings hardening via django-environ
# ---------------------------------------------------------------------------

class SettingsHardeningTest(TestCase):

    def test_prod_security_settings_active_when_debug_false(self):
        import os
        import importlib
        import dd3esheet.settings as settings_module
        from unittest.mock import patch

        with patch.dict(os.environ, {'DEBUG': 'False'}, clear=False):
            importlib.reload(settings_module)
            self.assertGreater(settings_module.SECURE_HSTS_SECONDS, 0)
            self.assertTrue(settings_module.SESSION_COOKIE_SECURE)
            self.assertTrue(settings_module.CSRF_COOKIE_SECURE)

        importlib.reload(settings_module)

    def test_secret_key_is_non_empty(self):
        from django.conf import settings as s
        self.assertTrue(len(s.SECRET_KEY) > 0)


# ---------------------------------------------------------------------------
# T0.2 — HTMX loaded in base template
# ---------------------------------------------------------------------------

class HtmxLoadedTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='HtmxTest')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})

    def test_character_page_includes_htmx_script(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        # WhiteNoise manifest storage appends content hashes (htmx.min.<hash>.js)
        self.assertContains(resp, 'htmx.min')

    def test_character_page_includes_csrf_config_request_handler(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'htmx:configRequest')


# ---------------------------------------------------------------------------
# T1.8 — <int:pk> URL converter
# ---------------------------------------------------------------------------

class UrlPkIntTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='UrlTest')
        _bootstrap_character_siblings(self.char)
        self.client.force_login(self.user)

    def test_non_numeric_pk_returns_404(self):
        resp = self.client.get('/character/character/abc')
        self.assertEqual(resp.status_code, 404)

    def test_numeric_pk_returns_200(self):
        resp = self.client.get(reverse('character:character', kwargs={'pk': self.char.pk}))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# T4.1 — Padronizar max-width das sub-páginas em 1280px
# ---------------------------------------------------------------------------

class SubPageWidthTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user(username='widthuser')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='WidthTest')
        _bootstrap_character_siblings(self.char)
        self.client.force_login(self.user)

    def _css_text(self):
        import re as _re
        css_path = settings.BASE_DIR / 'static' / 'css' / 'character_sheet.css'
        with open(css_path, encoding='utf-8') as f:
            return f.read()

    def test_companions_page_has_companions_sheet_class(self):
        url = reverse('character:companions', kwargs={'pk': self.char.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'companions-sheet')

    def test_daily_resources_page_has_sheet_utility_class(self):
        url = reverse('character:daily-resources', kwargs={'pk': self.char.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'sheet-utility')

    def test_reputation_page_has_sheet_utility_class(self):
        url = reverse('character:reputation', kwargs={'pk': self.char.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'sheet-utility')

    def test_companions_sheet_max_width_is_1280px(self):
        import re
        css = self._css_text()
        m = re.search(r'\.companions-sheet\s*\{([^}]+)\}', css)
        self.assertIsNotNone(m, '.companions-sheet rule not found in CSS')
        self.assertIn('1280px', m.group(1), '.companions-sheet max-width must be 1280px')

    def test_sheet_utility_max_width_is_1280px(self):
        import re
        css = self._css_text()
        m = re.search(r'\.sheet-utility\s*\{([^}]+)\}', css)
        self.assertIsNotNone(m, '.sheet-utility rule not found in CSS')
        self.assertIn('1280px', m.group(1), '.sheet-utility max-width must be 1280px')

    def test_buffs_panel_uses_available_lateral_space(self):
        # O painel de buffs deve ocupar o vao lateral disponivel antes da
        # tabela de pericias, nao ficar preso na largura da coluna de atributos.
        import re
        css = self._css_text()
        grid = re.search(r'\.main-grid\s*\{([^}]+)\}', css)
        area = re.search(r'\.abilities-area\s*\{([^}]+)\}', css)
        target = re.search(r'#characterBuffsForm\s*\{([^}]+)\}', css)
        panel = re.search(r'\.buffs-panel\s*\{([^}]+)\}', css)
        self.assertIsNotNone(grid, '.main-grid rule not found')
        self.assertIsNotNone(area, '.abilities-area rule not found')
        self.assertIsNotNone(target, '#characterBuffsForm rule not found')
        self.assertIsNotNone(panel, '.buffs-panel rule not found')
        self.assertRegex(grid.group(1), r'"buffs\s+buffs\s+skills"')
        self.assertIn('align-self', area.group(1))
        self.assertIn('grid-area: buffs', target.group(1))
        self.assertIn('flex', panel.group(1))

    def test_pv_current_temp_boxes_sit_side_by_side(self):
        # PV Atual e Temporario devem ficar lado a lado (2 colunas); sem
        # grid-template-columns o segundo quadrado cai para a linha de baixo.
        import re
        css = self._css_text()
        m = re.search(r'\.pv-current-temp\s*\{([^}]+)\}', css)
        self.assertIsNotNone(m, '.pv-current-temp rule not found in CSS')
        self.assertIn('grid-template-columns', m.group(1),
                      '.pv-current-temp precisa definir 2 colunas lado a lado')


# ---------------------------------------------------------------------------
# T4.2 — Renomear "Companheiros" → "Aliados" na UI
# ---------------------------------------------------------------------------

class AlliesRenameTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        setup_sdr_spell_table()
        self.user = make_user(username='aliasuser')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='AliasTest')
        _bootstrap_character_siblings(self.char)
        self.client.force_login(self.user)

    def test_companions_url_still_resolves(self):
        url = reverse('character:companions', kwargs={'pk': self.char.pk})
        self.assertEqual(url, f'/character/character/{self.char.pk}/companions')

    def test_companions_page_shows_aliados_not_companheiros(self):
        url = reverse('character:companions', kwargs={'pk': self.char.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Aliados')
        self.assertNotContains(resp, 'Companheiros')

    def test_main_sheet_nav_shows_aliados(self):
        url = reverse('character:character', kwargs={'pk': self.char.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Aliados')

    def test_daily_resources_nav_shows_aliados(self):
        url = reverse('character:daily-resources', kwargs={'pk': self.char.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Aliados')

    def test_reputation_nav_shows_aliados(self):
        url = reverse('character:reputation', kwargs={'pk': self.char.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Aliados')


# ---------------------------------------------------------------------------
# T4.3 — Redesign do bloco Nome do Aliado/Familiar
# ---------------------------------------------------------------------------

class CompanionNameLineTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user(username='namelineuser')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='NameLineTest')
        _bootstrap_character_siblings(self.char)
        self.client.force_login(self.user)

    def test_companions_page_has_name_line_class(self):
        url = reverse('character:companions', kwargs={'pk': self.char.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'companion-name-line')

    def test_companions_page_has_quickstats_class(self):
        url = reverse('character:companions', kwargs={'pk': self.char.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'companion-quickstats')


# ---------------------------------------------------------------------------
# T4.4 — Stack vertical + accordion Animal/Familiar
# ---------------------------------------------------------------------------

class CompanionCollapseTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        from .services import _bootstrap_character_siblings
        self.user_empty = make_user(username='collapseempty')
        self.char_empty = Character.objects.create(User=self.user_empty, Name='EmptyTest')
        _bootstrap_character_siblings(self.char_empty)

        self.user_named = make_user(username='collapsenamed')
        self.char_named = Character.objects.create(User=self.user_named, Name='NamedTest')
        _bootstrap_character_siblings(self.char_named)
        from .models import CharacterCompanion
        CharacterCompanion.objects.create(Character=self.char_named, Type='animal', Name='Rex')
        CharacterCompanion.objects.create(Character=self.char_named, Type='familiar', Name='Pyro')

    def test_empty_name_sections_start_collapsed(self):
        self.client.force_login(self.user_empty)
        url = reverse('character:companions', kwargs={'pk': self.char_empty.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-collapsed="true"')

    def test_companion_section_uses_companion_section_class(self):
        self.client.force_login(self.user_empty)
        url = reverse('character:companions', kwargs={'pk': self.char_empty.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'companion-section')

    def test_named_companion_section_not_collapsed(self):
        self.client.force_login(self.user_named)
        url = reverse('character:companions', kwargs={'pk': self.char_named.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotIn('data-collapsed="true"', content)


class CharacterSummonModelTest(TestCase):

    def test_default_ordering_uses_rounds_remaining_desc(self):
        user = make_user(username='summonmodel')
        char = make_character(user, 'Invoker')
        CharacterSummon.objects.create(Character=char, Name='Wolf', RoundsRemaining=2)
        CharacterSummon.objects.create(Character=char, Name='Bear', RoundsRemaining=6)

        names = list(CharacterSummon.objects.filter(Character=char).values_list('Name', flat=True))
        self.assertEqual(names, ['Bear', 'Wolf'])


class SummonsGridTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        setup_sdr_spell_table()
        self.user = make_user(username='summongrid')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Summoner')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:companions', kwargs={'pk': self.char.pk})
        self.client.force_login(self.user)

    def test_htmx_post_creates_three_summons_and_get_renders_three_cards(self):
        resp = self.client.post(
            self.url,
            {
                'summon_1_Name': 'Lobo',
                'summon_1_SpellOrigin': 'SNA II',
                'summon_1_RoundsTotal': '7',
                'summon_1_RoundsRemaining': '7',
                'summon_2_Name': 'Urso negro',
                'summon_2_SpellOrigin': 'SNA III',
                'summon_2_RoundsTotal': '7',
                'summon_2_RoundsRemaining': '6',
                'summon_3_Name': 'Corvo celestial',
                'summon_3_SpellOrigin': 'SM I',
                'summon_3_RoundsTotal': '5',
                'summon_3_RoundsRemaining': '4',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='summonsGrid',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(CharacterSummon.objects.filter(Character=self.char).count(), 3)
        page = self.client.get(self.url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'data-summon-card="active"', count=3)

    def test_summon_cards_render_paper_style_blank_fields(self):
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-sheet-table="summon-active-card"', count=3)
        self.assertContains(resp, 'class="summon-stat-table"', count=3)
        self.assertContains(resp, 'data-field="summon.Name"', count=3)
        self.assertContains(resp, 'data-field="summon.Initiative"', count=3)
        self.assertContains(resp, 'data-field="summon.Speed"', count=3)
        self.assertContains(resp, 'data-field="summon.BaseAttackBonus"', count=3)
        self.assertContains(resp, 'data-field="summon.Grapple"', count=3)
        self.assertContains(resp, 'data-field="summon.Size"', count=3)
        self.assertContains(resp, 'data-field="summon.Attack"', count=3)
        self.assertContains(resp, 'data-field="summon.FullAttack"', count=3)
        self.assertContains(resp, 'data-field="summon.Skills"', count=3)
        self.assertContains(resp, 'data-field="summon.SpecialAbility"', count=3)
        self.assertContains(resp, 'aria-label="Espaco para observacoes da invocacao"', count=3)

    def test_htmx_post_persists_full_stat_block_fields(self):
        resp = self.client.post(
            self.url,
            {
                'summon_1_Name': 'Urso atroz',
                'summon_1_Initiative': '+1',
                'summon_1_Speed': '12m',
                'summon_1_ArmorClass': '17',
                'summon_1_BaseAttackBonus': '+9',
                'summon_1_Grapple': '+23',
                'summon_1_Size': 'Grande',
                'summon_1_Attack': 'Garra +19 (2d4+10)',
                'summon_1_FullAttack': '2x Garras +19 (2d4+10) e Mordida +13 (2d8+5)',
                'summon_1_Skills': 'Ouvir +10, Observar +10, Natacao +13',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='summonsGrid',
        )

        self.assertEqual(resp.status_code, 200)
        summon = CharacterSummon.objects.get(Character=self.char)
        self.assertEqual(summon.Initiative, '+1')
        self.assertEqual(summon.Speed, '12m')
        self.assertEqual(summon.BaseAttackBonus, '+9')
        self.assertEqual(summon.Grapple, '+23')
        self.assertEqual(summon.Size, 'Grande')
        self.assertEqual(summon.Attack, 'Garra +19 (2d4+10)')
        self.assertEqual(summon.FullAttack, '2x Garras +19 (2d4+10) e Mordida +13 (2d8+5)')
        self.assertEqual(summon.Skills, 'Ouvir +10, Observar +10, Natacao +13')


class SummonHighlightToggleTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        setup_sdr_spell_table()
        self.user = make_user(username='summonhl')
        self.other = make_user(username='summonother')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Highlighter')
        _bootstrap_character_siblings(self.char)
        self.first = CharacterSummon.objects.create(Character=self.char, Name='Wolf', RoundsRemaining=2)
        self.second = CharacterSummon.objects.create(Character=self.char, Name='Bear', RoundsRemaining=5)

    def test_toggle_flips_highlight_and_moves_summon_to_top(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse('character:toggle-summon-highlight', kwargs={'pk': self.char.pk, 'summon_id': self.first.pk}),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(resp.status_code, 200)
        self.first.refresh_from_db()
        self.assertTrue(self.first.Highlighted)
        ordered = list(CharacterSummon.objects.filter(Character=self.char).values_list('Name', flat=True))
        self.assertEqual(ordered[0], 'Wolf')
        self.assertTemplateUsed(resp, 'character/partials/companions_summons_grid.html')

    def test_non_owner_gets_404(self):
        self.client.force_login(self.other)
        resp = self.client.post(
            reverse('character:toggle-summon-highlight', kwargs={'pk': self.char.pk, 'summon_id': self.first.pk}),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp.status_code, 404)


class SummonAutocompleteTests(TransactionTestCase):
    databases = {'default', 'sdr'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_sdr_monster_table()

    def setUp(self):
        setup_sdr_class_table()
        setup_sdr_spell_table()
        SDR_Monster.objects.using('sdr').all().delete()
        self.monster = SDR_Monster.objects.using('sdr').create(
            name='Wolf',
            size='Medium',
            hit_dice='2d8+4 (13 hp)',
            initiative='+2',
            speed='50 ft.',
            armor_class='14',
            base_attack='+1',
            grapple='+2',
            attack='Bite +3 melee (1d6+1)',
            full_attack='Bite +3 melee (1d6+1)',
            skills='Hide +2, Listen +3, Move Silently +3, Spot +3',
            special_abilities='Trip',
        )
        self.user = make_user(username='summonsearch')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Searcher')
        _bootstrap_character_siblings(self.char)
        self.client.force_login(self.user)

    def test_search_returns_hits_for_two_character_query(self):
        resp = self.client.get(reverse('character:summon-search', kwargs={'pk': self.char.pk}), {'q': 'wo'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Wolf')

    def test_create_from_monster_persists_sdr_name_and_stats(self):
        resp = self.client.post(
            reverse('character:create-summon-from-monster', kwargs={'pk': self.char.pk, 'monster_id': self.monster.pk}),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(resp.status_code, 200)
        summon = CharacterSummon.objects.get(Character=self.char)
        self.assertEqual(summon.Name, 'Wolf')
        self.assertEqual(summon.SdrMonsterName, 'Wolf')
        self.assertEqual(summon.HitPointsMax, 13)
        self.assertEqual(summon.HitPointsCurrent, 13)
        self.assertEqual(summon.ArmorClass, 14)
        self.assertEqual(summon.AttackBonus, '+3')
        self.assertEqual(summon.Damage, '1d6+1')
        self.assertEqual(summon.Size, 'Medium')
        self.assertEqual(summon.Initiative, '+2')
        self.assertEqual(summon.Speed, '50 ft.')
        self.assertEqual(summon.BaseAttackBonus, '+1')
        self.assertEqual(summon.Grapple, '+2')
        self.assertEqual(summon.Attack, 'Bite +3 melee (1d6+1)')
        self.assertEqual(summon.FullAttack, 'Bite +3 melee (1d6+1)')
        self.assertEqual(summon.Skills, 'Hide +2, Listen +3, Move Silently +3, Spot +3')
        self.assertEqual(summon.SpecialAbility, 'Trip')

    def test_short_or_missing_query_returns_empty_without_500(self):
        short_resp = self.client.get(reverse('character:summon-search', kwargs={'pk': self.char.pk}), {'q': 'w'})
        none_resp = self.client.get(reverse('character:summon-search', kwargs={'pk': self.char.pk}), {'q': 'zzzz'})

        self.assertEqual(short_resp.status_code, 200)
        self.assertEqual(none_resp.status_code, 200)
        self.assertEqual(short_resp.content, b'')
        self.assertEqual(none_resp.content.strip(), b'')


# ---------------------------------------------------------------------------
# T3 — SDRSpellId column
# ---------------------------------------------------------------------------

class CharacterSpellSDRLinkTests(TestCase):
    databases = {'sdr', 'default'}

    def test_sdr_spell_id_nullable_by_default(self):
        user = make_user()
        char = make_character(user)
        spell = CharacterSpell.objects.create(Character=char, Name="X", Level=1)
        self.assertIsNone(spell.SDRSpellId)

    def test_sdr_spell_id_stores_integer(self):
        user = make_user()
        char = make_character(user)
        spell = CharacterSpell.objects.create(
            Character=char, Name="Magic Missile", Level=1, SDRSpellId=42,
        )
        spell.refresh_from_db()
        self.assertEqual(spell.SDRSpellId, 42)


class SpellbookSDRResolveTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_sdr_spell_table()

    def setUp(self):
        from sdr.models import SDR_Spell
        SDR_Spell.objects.using('sdr').all().delete()
        self.sdr_mm = SDR_Spell(
            name="Magic Missile", altname="Misseis Magicos",
            school="Evocation", level="Sor/Wiz 1",
            short_description="1 missil mais 1 a cada dois niveis",
        )
        self.sdr_mm.save(using='sdr')
        self.user = make_user()
        self.char = make_character(self.user)
        self.client.force_login(self.user)

    def _post_level(self, level, rows):
        data = {}
        for i, (name, page) in enumerate(rows, start=1):
            data[f'spellbook_{level}_{i}_Name'] = name
            data[f'spellbook_{level}_{i}_Page'] = page
        return self.client.post(
            reverse('character:spellbook', args=[self.char.pk]),
            data=data,
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET=f'spellbookLevel{level}Form',
        )

    def test_save_resolves_sdr_id_for_known_spell(self):
        self._post_level(1, [("Magic Missile", "12")])
        spell = CharacterSpell.objects.get(Character=self.char, Level=1)
        self.assertEqual(spell.SDRSpellId, self.sdr_mm.id)

    def test_save_resolves_sdr_id_by_altname(self):
        self._post_level(1, [("Misseis Magicos", "")])
        spell = CharacterSpell.objects.get(Character=self.char, Level=1)
        self.assertEqual(spell.SDRSpellId, self.sdr_mm.id)

    def test_save_leaves_sdr_id_none_for_homebrew(self):
        self._post_level(1, [("Bola de Fogo Tropical", "")])
        spell = CharacterSpell.objects.get(Character=self.char, Level=1)
        self.assertIsNone(spell.SDRSpellId)

    def test_save_clears_sdr_id_when_switching_to_homebrew(self):
        self._post_level(1, [("Magic Missile", "")])
        self._post_level(1, [("Bola de Fogo Tropical", "")])
        spell = CharacterSpell.objects.get(Character=self.char, Level=1)
        self.assertIsNone(spell.SDRSpellId)


# ---------------------------------------------------------------------------
# T9 — spellbook render: sdr_lookup, tooltip, trigger, datalist
# ---------------------------------------------------------------------------

class SpellbookLevelRenderTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_sdr_spell_table()

    def setUp(self):
        from sdr.models import SDR_Spell
        SDR_Spell.objects.using('sdr').all().delete()
        self.sdr_mm = SDR_Spell(
            name="Magic Missile", school="Evocation", level="Sor/Wiz 1",
            casting_time="1 ação padrão",
            short_description="1 missil mais 1 a cada 2 niveis",
        )
        self.sdr_mm.save(using='sdr')
        self.user = make_user(); self.user.set_password('pw'); self.user.save()
        self.char = make_character(self.user)
        self.client.force_login(self.user)

    def test_known_spell_renders_data_sdr_id_and_trigger(self):
        CharacterSpell.objects.create(
            Character=self.char, Name="Magic Missile", Level=1, SDRSpellId=self.sdr_mm.id,
        )
        url = reverse('character:spellbook', args=[self.char.pk])
        resp = self.client.get(url)
        body = resp.content.decode()
        self.assertIn(f'data-sdr-id="{self.sdr_mm.id}"', body)
        self.assertIn('class="spell-detail-trigger"', body)
        self.assertIn('class="spell-tooltip"', body)
        self.assertIn('1 missil mais 1 a cada 2 niveis', body)

    def test_homebrew_spell_renders_without_sdr_attrs(self):
        CharacterSpell.objects.create(
            Character=self.char, Name="Bola Tropical", Level=1, SDRSpellId=None,
        )
        url = reverse('character:spellbook', args=[self.char.pk])
        body = self.client.get(url).content.decode()
        self.assertNotIn('spell-detail-trigger', body)
        self.assertNotIn('class="spell-tooltip"', body)

    def test_datalist_is_rendered_once(self):
        url = reverse('character:spellbook', args=[self.char.pk])
        body = self.client.get(url).content.decode()
        self.assertEqual(body.count('id="spell-suggestions"'), 1)
        self.assertIn('value="Magic Missile"', body)


# ---------------------------------------------------------------------------
# T5 — spell_detail view
# ---------------------------------------------------------------------------

class SpellDetailViewTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_sdr_spell_table()

    def setUp(self):
        from sdr.models import SDR_Spell
        SDR_Spell.objects.using('sdr').all().delete()
        self.spell = SDR_Spell(
            name="Magic Missile",
            full_text="<p>Conjuras misseis magicos.</p>",
            school="Evocation", level="Sor/Wiz 1",
        )
        self.spell.save(using='sdr')
        self.owner = make_user('owner')
        self.owner.set_password('pw'); self.owner.save()
        self.stranger = make_user('stranger')
        self.stranger.set_password('pw'); self.stranger.save()
        self.char = make_character(self.owner)

    def test_owner_gets_dialog_partial(self):
        self.client.force_login(self.owner)
        url = reverse('character:spell-detail', args=[self.char.pk, self.spell.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Magic Missile', resp.content)
        self.assertIn(b'Conjuras misseis magicos', resp.content)

    def test_unknown_sdr_id_returns_404(self):
        self.client.force_login(self.owner)
        url = reverse('character:spell-detail', args=[self.char.pk, 99999])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_stranger_gets_404(self):
        self.client.force_login(self.stranger)
        url = reverse('character:spell-detail', args=[self.char.pk, self.spell.id])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_anonymous_redirected_or_blocked(self):
        url = reverse('character:spell-detail', args=[self.char.pk, self.spell.id])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (302, 401, 403))


# ---------------------------------------------------------------------------
# T10 — domain_spells includes sdr_id
# ---------------------------------------------------------------------------

def setup_sdr_domain_table():
    with connections['sdr'].cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                granted_powers TEXT,
                spell_1 TEXT, spell_2 TEXT, spell_3 TEXT, spell_4 TEXT,
                spell_5 TEXT, spell_6 TEXT, spell_7 TEXT, spell_8 TEXT, spell_9 TEXT,
                full_text TEXT,
                reference TEXT
            )
        """)


class DomainSpellsResolveTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_sdr_spell_table()
        setup_sdr_domain_table()

    def test_domain_spells_includes_sdr_id_when_known(self):
        from sdr.models import SDR_Spell, SDR_Domain
        from character.spellcasting import domain_spells
        SDR_Spell.objects.using('sdr').all().delete()
        SDR_Domain.objects.using('sdr').all().delete()
        sdr = SDR_Spell(name="Bless", school="Enchantment", level="Clr 1")
        sdr.save(using='sdr')
        d = SDR_Domain(name="Good", spell_1="Bless")
        d.save(using='sdr')
        rows = domain_spells("Good")
        row1 = next(r for r in rows if r['level'] == 1)
        self.assertEqual(row1['name'], "Bless")
        self.assertEqual(row1['sdr_id'], sdr.id)

    def test_domain_spells_sdr_id_none_when_unknown(self):
        from sdr.models import SDR_Spell, SDR_Domain
        from character.spellcasting import domain_spells
        SDR_Spell.objects.using('sdr').all().delete()
        SDR_Domain.objects.using('sdr').all().delete()
        d = SDR_Domain(name="Custom", spell_1="Homebrew Spell")
        d.save(using='sdr')
        rows = domain_spells("Custom")
        row1 = next(r for r in rows if r['level'] == 1)
        self.assertEqual(row1['name'], "Homebrew Spell")
        self.assertIsNone(row1['sdr_id'])


# ---------------------------------------------------------------------------
# T11 — _summon_nature_rows includes sdr_id
# ---------------------------------------------------------------------------

class SummonNatureRowsResolveTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_sdr_spell_table()

    def test_summon_rows_have_sdr_id_when_known(self):
        from sdr.models import SDR_Spell
        from character.views import _summon_nature_rows
        SDR_Spell.objects.using('sdr').all().delete()
        sdr = SDR_Spell(
            name="Aliado da Natureza I",
            altname="Summon Nature's Ally I",
            school="Conjuration", level="Drd 1",
        )
        sdr.save(using='sdr')
        rows = _summon_nature_rows()
        row1 = next(r for r in rows if r['level'] == 1)
        self.assertEqual(row1['sdr_id'], sdr.id)

    def test_summon_rows_sdr_id_none_when_unknown(self):
        from sdr.models import SDR_Spell
        from character.views import _summon_nature_rows
        SDR_Spell.objects.using('sdr').all().delete()
        rows = _summon_nature_rows()
        self.assertTrue(all(r['sdr_id'] is None for r in rows))


# ---------------------------------------------------------------------------
# Entrega B — Autosave: POST with HX-Autosave header → 204, no re-render
# ---------------------------------------------------------------------------

class AutosaveOnInputTest(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_sdr_class_table()
        setup_sdr_spell_table()

    def setUp(self):
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Autosave Test')
        _bootstrap_character_siblings(self.char)
        self.client.force_login(self.user)

    def _autosave_post(self, url, target, data):
        return self.client.post(
            url,
            data=data,
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET=target,
            HTTP_HX_AUTOSAVE='1',
        )

    def test_feats_autosave_returns_204_and_persists(self):
        url = reverse('character:character', args=[self.char.pk])
        resp = self._autosave_post(url, 'characterFeatsForm', {
            'feat_1_Name': 'Iniciativa Aprimorada',
            'feat_1_Page': '100',
        })
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b'')
        from .models import CharacterFeat
        feat = CharacterFeat.objects.filter(Character=self.char).first()
        self.assertIsNotNone(feat)
        self.assertEqual(feat.Name, 'Iniciativa Aprimorada')

    def test_specials_autosave_returns_204_and_persists(self):
        url = reverse('character:character', args=[self.char.pk])
        resp = self._autosave_post(url, 'characterSpecialsForm', {
            'ability_1_Name': 'Missão Épica',
            'ability_1_Page': '50',
        })
        self.assertEqual(resp.status_code, 204)
        from .models import Ability
        ability = Ability.objects.filter(Character=self.char).first()
        self.assertIsNotNone(ability)
        self.assertEqual(ability.Name, 'Missão Épica')

    def test_reputation_contacts_autosave_returns_204_and_persists(self):
        url = reverse('character:reputation', args=[self.char.pk])
        resp = self._autosave_post(url, 'reputationContactsForm', {
            'contact_1_Name': 'Tharivol',
            'contact_1_Location': 'Waterdeep',
            'contact_1_Relationship': 'Aliado',
        })
        self.assertEqual(resp.status_code, 204)
        from .models import CharacterContact
        contact = CharacterContact.objects.filter(Character=self.char).first()
        self.assertIsNotNone(contact)
        self.assertEqual(contact.Name, 'Tharivol')

    def test_derived_field_without_autosave_header_still_renders(self):
        url = reverse('character:character', args=[self.char.pk])
        resp = self.client.post(
            url,
            data={'feat_1_Name': 'Power Attack', 'feat_1_Page': '98'},
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterFeatsForm',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.content), 0)


# ---------------------------------------------------------------------------
# Retrabalho B — AutosaveCoverageTest: P1.1, P1.2 e P2
# ---------------------------------------------------------------------------

class AutosaveCoverageTest(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        setup_sdr_spell_table()
        from sdr.models import SDR_Spell
        SDR_Spell.objects.using('sdr').all().delete()
        self.mm = SDR_Spell(name='Magic Missile', school='Evocation', level='Sor/Wiz 1')
        self.mm.save(using='sdr')
        self.user = make_user()
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Coverage', Class='Fighter', Level='1')
        _bootstrap_character_siblings(self.char)
        self.client.force_login(self.user)

    def _autosave(self, url, target, data):
        return self.client.post(url, data=data,
            HTTP_HX_REQUEST='true', HTTP_HX_TARGET=target, HTTP_HX_AUTOSAVE='1')

    def _blur(self, url, target, data):
        return self.client.post(url, data=data,
            HTTP_HX_REQUEST='true', HTTP_HX_TARGET=target)

    # P1.1 — daily_resources
    def test_daily_resources_autosave_returns_204_and_persists(self):
        from .models import CharacterDailyNotes
        url = reverse('character:daily-resources', args=[self.char.pk])
        resp = self._autosave(url, 'dailyResourcesForm', {'Preparation': 'Orar ao acordar'})
        self.assertEqual(resp.status_code, 204)
        notes = CharacterDailyNotes.objects.get(Character=self.char)
        self.assertEqual(notes.Preparation, 'Orar ao acordar')

    def test_daily_resources_blur_returns_200_and_rerenders(self):
        url = reverse('character:daily-resources', args=[self.char.pk])
        resp = self._blur(url, 'dailyResourcesForm', {'Preparation': 'Planejar missao'})
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.content), 0)

    # P1.2 — spellbook level autosave + blur re-render
    def test_spellbook_level_autosave_returns_204_and_persists(self):
        url = reverse('character:spellbook', args=[self.char.pk])
        resp = self._autosave(url, 'spellbookLevel1Form', {
            'spellbook_1_1_Name': 'Fireball',
            'spellbook_1_1_Page': '275',
        })
        self.assertEqual(resp.status_code, 204)
        spell = CharacterSpell.objects.filter(Character=self.char, Level=1).first()
        self.assertIsNotNone(spell)
        self.assertEqual(spell.Name, 'Fireball')

    def test_spellbook_level_blur_returns_200_and_reveals_sdr_trigger(self):
        url = reverse('character:spellbook', args=[self.char.pk])
        resp = self._blur(url, 'spellbookLevel1Form', {
            'spellbook_1_1_Name': 'Magic Missile',
            'spellbook_1_1_Page': '251',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'spell-detail-trigger', resp.content)

    # P2 — formularios sem calculo visivel mantem autosave leve (204) ao digitar
    def test_data_forms_autosave_returns_204(self):
        url = reverse('character:character', args=[self.char.pk])
        cases = [
            ('characterIdentityForm', {
                'Name': 'Coverage', 'Class': 'Fighter', 'Level': '1',
                'Race': '', 'Alignment': '', 'Deity': '', 'Size': '',
                'Age': '', 'Sex': '', 'Heigth': '', 'Weight': '',
                'Eye': '', 'Hair': '', 'Skin': '',
            }),
            ('characterStatusForm', {'TotalHitPoints': '20'}),
            ('characterWeaponsForm', {'weapon_1_Attack': 'Longsword'}),
            ('characterEquipmentForm', {'armor_Name': 'Chain Shirt'}),
            ('characterItemsForm', {'item_1_Name': 'Rope'}),
            ('characterMoneyForm', {'GP': '30'}),
        ]
        for target, payload in cases:
            with self.subTest(target=target):
                resp = self._autosave(url, target, payload)
                self.assertEqual(resp.status_code, 204, f'Expected 204 for {target}')

    # P2 — formularios com calculo visivel re-renderizam ao vivo, ja ao digitar
    # (input/autosave), nao so no blur. Reproduz "digitei 12 e o mod nao virou 1".
    def test_calc_forms_autosave_renders_recalculated_values(self):
        url = reverse('character:character', args=[self.char.pk])
        for target in ('characterSavesForm', 'characterAttackForm',
                       'characterArmorForm', 'characterSkillsForm'):
            with self.subTest(target=target):
                resp = self._autosave(url, target, {})
                self.assertEqual(resp.status_code, 200, f'Expected 200 for {target}')
                self.assertGreater(len(resp.content), 0)
        resp = self._autosave(url, 'characterStatsForm', {
            'Strength': '12', 'Dexterity': '10', 'Constitution': '10',
            'Intelligence': '10', 'Wisdom': '10', 'Charisma': '10',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertRegex(resp.content.decode(), r'data-derived="StrengthStatMod"[^>]*>\s*1\s*<')

    def test_recalculating_forms_blur_still_returns_200(self):
        url = reverse('character:character', args=[self.char.pk])
        cases = [
            ('characterStatsForm', {'Strength': '14'}),
            ('characterStatusForm', {'TotalHitPoints': '20'}),
            ('characterEquipmentForm', {'armor_Name': 'Chain Shirt'}),
            ('characterItemsForm', {'item_1_Name': 'Rope'}),
            ('characterMoneyForm', {'GP': '30'}),
        ]
        for target, payload in cases:
            with self.subTest(target=target):
                resp = self._blur(url, target, payload)
                self.assertEqual(resp.status_code, 200)
                self.assertGreater(len(resp.content), 0)


# ---------------------------------------------------------------------------
# fix/agent1-correcoes — bugs de layout e cálculo
# ---------------------------------------------------------------------------

class CharacterLayoutBugFixTests(TransactionTestCase):
    """Cobertura para os 4 bugs: AbilityModifier, PV/CA duplicação, CA cinza, Saves layout."""
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user(username='layoutfix')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='LayoutTest')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})
        self.client.force_login(self.user)

    def _post_htmx(self, target, data=None):
        return self.client.post(
            self.url, data or {},
            HTTP_HX_REQUEST='true', HTTP_HX_TARGET=target,
        )

    # Bug 1 — AbilityModifier calculado ao vivo, sem depender do DB
    def test_skills_show_ability_modifier_computed_from_stats(self):
        skill = CharacterSkill.objects.get(Character=self.char, SkillName='Escalar')
        skill.AbilityModifier = 0
        skill.save()
        self.char.characterstats.Strength = 16
        self.char.characterstats.save()

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        import re
        content = resp.content.decode()
        matches = re.findall(r'data-derived="AbilityModifier"[^>]*>\s*3\s*<', content)
        self.assertGreater(len(matches), 0,
            'Esperava AbilityModifier=3 para Escalar (Strength=16) no HTML')

    # Mod. de habilidade 0 (atributo = 10) precisa aparecer como "0", nao "-".
    # O filtro |default trata 0 como vazio; derivados numericos usam |default_if_none.
    def test_derived_zero_renders_as_zero_not_dash(self):
        resp = self._post_htmx('characterStatsForm', {
            'Strength': '10', 'Dexterity': '10', 'Constitution': '10',
            'Intelligence': '10', 'Wisdom': '10', 'Charisma': '10',
        })
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertRegex(content, r'data-derived="StrengthStatMod"[^>]*>\s*0\s*<')
        # save total derivado tambem deve mostrar 0
        self.assertRegex(content, r'data-derived="TotalFortitude"[^>]*>\s*0\s*<')

    # Logs diagnosticos: o POST e o recalculo devem explicar o que aconteceu,
    # inclusive POR QUE um mod efetivo sai baixo (VALOR TEMPORARIO sobrescreve).
    def test_stats_post_emits_diagnostic_logs(self):
        with self.assertLogs('character', level='DEBUG') as cm:
            self._post_htmx('characterStatsForm', {'Strength': '14', 'StrengthTemp': '4', 'StrengthModTemp': '1'})
        blob = '\n'.join(cm.output)
        self.assertIn('sheet POST', blob)
        self.assertIn('recalc done', blob)
        # a decisao por habilidade aparece com os ajustes temporarios e o mod final
        self.assertRegex(blob, r'Strength base=14 \+valorTemp=4 \+modTemp=1 \+buff=0 -> mod=\+5')

    # Habilidade em branco (score 0/nao preenchido) deve mostrar "-" no mod,
    # nunca -5 (que seria mod de um score 0 real). Caixa de valor vazia -> mod vazio.
    def test_blank_ability_score_shows_dash_not_minus_five(self):
        resp = self._post_htmx('characterStatsForm', {
            'Strength': '', 'Dexterity': '', 'Constitution': '',
            'Intelligence': '', 'Wisdom': '', 'Charisma': '',
        })
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotRegex(content, r'data-derived="StrengthStatMod"[^>]*>\s*-5\s*<')
        self.assertRegex(content, r'data-derived="StrengthStatMod"[^>]*>\s*-\s*<')
        self.char.characterstats.refresh_from_db()
        self.assertIsNone(self.char.characterstats.StrengthStatMod)

    # O form editado e o swap principal; as secoes derivadas voltam como
    # out-of-band (hx-swap-oob) para atualizar na tela sem duplicar/aninhar.
    def test_status_form_swap_refreshes_dependent_sections_as_oob(self):
        resp = self._post_htmx('characterStatusForm', {'TotalHitPoints': '30'})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # swap principal: aparece uma unica vez e sem marca de OOB
        self.assertEqual(content.count('id="characterStatusForm"'), 1)
        self.assertNotIn('id="characterStatusForm" hx-swap-oob', content)
        # secoes dependentes voltam como OOB
        self.assertIn('id="characterArmorForm" hx-swap-oob="true"', content)
        self.assertIn('id="characterSkillsForm" hx-swap-oob="true"', content)

    def test_armor_form_swap_refreshes_dependent_sections_as_oob(self):
        resp = self._post_htmx('characterArmorForm', {'ACSizeModifier': '0'})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertEqual(content.count('id="characterArmorForm"'), 1)
        self.assertNotIn('id="characterArmorForm" hx-swap-oob', content)
        self.assertIn('id="characterStatusForm" hx-swap-oob="true"', content)
        self.assertIn('id="characterDefenseSummary" data-sheet-table="defense-summary" hx-swap-oob="true"', content)

    # Bug 3 — ACArmorBonus/ACShieldBonus/ACMiscModifier são somente-leitura
    def test_armor_ac_fields_are_readonly_calc_not_inputs(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotIn('name="ACArmorBonus"', content)
        self.assertNotIn('name="ACShieldBonus"', content)
        self.assertNotIn('name="ACMiscModifier"', content)
        self.assertIn('data-derived="ACArmorBonus"', content)
        self.assertIn('data-derived="ACShieldBonus"', content)

    # Bonus de Ataque (arma) e Agarrar-BBA sao auto-derivados: o recalculo os
    # sobrescreve, entao nao podem ser inputs editaveis (o valor digitado seria
    # descartado). Viram celulas de calculo somente-leitura.
    def test_weapon_attack_bonus_is_readonly_derived_not_input(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotIn('name="weapon_1_AttackBonus"', content)
        self.assertIn('data-derived="weapon.AttackBonus"', content)

    def test_grappler_bba_is_readonly_derived_not_input(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertNotIn('name="GrapplerBBA"', content)
        self.assertIn('data-derived="GrapplerBBA"', content)

    def test_saves_form_swap_refreshes_dependent_sections_as_oob(self):
        resp = self._post_htmx('characterSavesForm', {'FortitudeBaseSave': '2'})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertEqual(content.count('id="characterSavesForm"'), 1)
        self.assertNotIn('id="characterSavesForm" hx-swap-oob', content)
        self.assertIn('id="characterStatsForm" hx-swap-oob="true"', content)
        self.assertIn('id="characterAttackForm" hx-swap-oob="true"', content)

    def test_attack_form_swap_refreshes_dependent_sections_as_oob(self):
        resp = self._post_htmx('characterAttackForm', {'BBA': '5'})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertEqual(content.count('id="characterAttackForm"'), 1)
        self.assertNotIn('id="characterAttackForm" hx-swap-oob', content)
        self.assertIn('id="characterSavesForm" hx-swap-oob="true"', content)

    def test_stats_form_swap_refreshes_dependent_sections_as_oob(self):
        resp = self._post_htmx('characterStatsForm', {'Strength': '14'})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertEqual(content.count('id="characterStatsForm"'), 1)
        self.assertNotIn('id="characterStatsForm" hx-swap-oob', content)
        self.assertIn('id="characterSavesForm" hx-swap-oob="true"', content)


class CharacterBuffTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
        self.user = make_user(username='buffs')
        from .services import _bootstrap_character_siblings
        self.char = Character.objects.create(User=self.user, Name='Buffer')
        _bootstrap_character_siblings(self.char)
        self.url = reverse('character:character', kwargs={'pk': self.char.pk})
        self.client.force_login(self.user)

    def test_active_ability_buff_raises_effective_modifier_and_cascades(self):
        from .views import _recalculate_stats
        from .models import CharacterBuff
        s = self.char.characterstats
        s.Strength = 14
        s.save()
        CharacterBuff.objects.create(
            Character=self.char, Name='Forca do Touro', StrengthBonus=4, IsActive=True)
        _recalculate_stats(self.char)
        s.refresh_from_db()
        # base 14 (+2) + buff +4 no score = 18 -> +4
        self.assertEqual(s.StrengthStatMod, 4)
        # cascata: agarrar usa a FOR efetiva
        self.char.characterattackmodifiers.refresh_from_db()
        self.assertEqual(self.char.characterattackmodifiers.GrapplerStrModifier, 4)
        # cascata: pericia de FOR
        escalar = CharacterSkill.objects.get(Character=self.char, SkillName='Escalar')
        self.assertEqual(escalar.AbilityModifier, 4)

    def test_inactive_buff_has_no_effect(self):
        from .views import _recalculate_stats
        from .models import CharacterBuff
        s = self.char.characterstats
        s.Strength = 14
        s.save()
        CharacterBuff.objects.create(
            Character=self.char, Name='Forca do Touro', StrengthBonus=4, IsActive=False)
        _recalculate_stats(self.char)
        s.refresh_from_db()
        self.assertEqual(s.StrengthStatMod, 2)

    def test_flat_buffs_apply_to_attack_ac_and_saves(self):
        from .views import _recalculate_stats
        from .models import CharacterBuff
        CharacterWeapon.objects.create(
            Character=self.char, Name='Espada', Attack='Espada', Range='-', Type='Corte')
        s = self.char.characterstats
        s.Strength = 14
        s.save()
        status = self.char.characterstatus
        # baseline sem buff
        _recalculate_stats(self.char)
        status.refresh_from_db()
        ac_base = status.ACTotal
        CharacterBuff.objects.create(
            Character=self.char, Name='Heroismo', AttackBonus=2, ACBonus=2, SaveBonus=2, IsActive=True)
        _recalculate_stats(self.char)
        weapon = CharacterWeapon.objects.get(Character=self.char)
        # ataque corpo-a-corpo: BBA(0) + FOR(+2) + tamanho(0) + buff(+2) = +4
        self.assertEqual(weapon.AttackBonus, '+4')
        status.refresh_from_db()
        self.char.charactersavingthrows.refresh_from_db()
        self.assertEqual(status.ACTotal, ac_base + 2)
        # Reflexos: base 0 + DES mod 0 + buff salvas 2 = 2
        self.assertEqual(self.char.charactersavingthrows.TotalReflex, 2)

    def test_toggle_buff_endpoint_flips_active_and_recalculates(self):
        from .models import CharacterBuff
        s = self.char.characterstats
        s.Strength = 14
        s.save()
        buff = CharacterBuff.objects.create(
            Character=self.char, Name='Forca do Touro', StrengthBonus=4, IsActive=False)
        resp = self.client.post(
            reverse('character:toggle-buff', kwargs={'pk': self.char.pk, 'buff_id': buff.id}),
            HTTP_HX_REQUEST='true', HTTP_HX_TARGET='characterBuffsForm',
        )
        self.assertEqual(resp.status_code, 200)
        buff.refresh_from_db()
        self.assertTrue(buff.IsActive)
        s.refresh_from_db()
        self.assertEqual(s.StrengthStatMod, 4)
        # cascata OOB: a tabela de atributos volta na resposta
        self.assertIn('id="characterStatsForm"', resp.content.decode())

    def test_add_buff_from_preset_creates_inactive_buff(self):
        from .models import CharacterBuff
        resp = self.client.post(
            reverse('character:add-buff', kwargs={'pk': self.char.pk}),
            {'preset': 'Agilidade do Gato'},
            HTTP_HX_REQUEST='true', HTTP_HX_TARGET='characterBuffsForm',
        )
        self.assertEqual(resp.status_code, 200)
        buff = CharacterBuff.objects.get(Character=self.char, Name='Agilidade do Gato')
        self.assertEqual(buff.DexterityBonus, 4)
        self.assertFalse(buff.IsActive)

    def test_delete_buff_removes_and_recalculates(self):
        from .models import CharacterBuff
        buff = CharacterBuff.objects.create(
            Character=self.char, Name='Forca do Touro', StrengthBonus=4, IsActive=True)
        resp = self.client.post(
            reverse('character:delete-buff', kwargs={'pk': self.char.pk, 'buff_id': buff.id}),
            HTTP_HX_REQUEST='true', HTTP_HX_TARGET='characterBuffsForm',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CharacterBuff.objects.filter(id=buff.id).exists())

    def test_buffs_panel_renders_on_character_sheet(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="characterBuffsForm"')

    def test_buff_actions_require_owner(self):
        from .models import CharacterBuff
        buff = CharacterBuff.objects.create(Character=self.char, Name='X', IsActive=False)
        other = make_user(username='intruder')
        self.client.force_login(other)
        resp = self.client.post(
            reverse('character:toggle-buff', kwargs={'pk': self.char.pk, 'buff_id': buff.id}),
            HTTP_HX_REQUEST='true', HTTP_HX_TARGET='characterBuffsForm',
        )
        self.assertEqual(resp.status_code, 404)
