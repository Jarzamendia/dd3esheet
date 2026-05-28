from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.db import connections
from django.urls import reverse

from .models import (
    Character, CharacterStats, CharacterStatus, CharacterSavingThrows,
    CharacterAttackModifiers, CharacterSkillGraduation, CharacterOtherItemObs,
    CharacterMoney, CharacterSpellSave, CharacterArcaneSpellFailCheck,
    CharacterMagicConditionalModifiers, CharacterSkill, CharacterWeapon,
    CharacterArmor, CharacterShield, CharacterProtectionItem,
    CharacterSpellcasting, CharacterSpellSlot, CharacterSpell, CharacterFeat,
)
from sdr.models import SDR_Class


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
        self.assertTrue(CharacterSpellSave.objects.filter(Character=char).exists())
        self.assertTrue(CharacterArcaneSpellFailCheck.objects.filter(Character=char).exists())
        self.assertTrue(CharacterMagicConditionalModifiers.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSpellcasting.objects.filter(Character=char).exists())
        self.assertEqual(CharacterSkill.objects.filter(Character=char).count(), 35)


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
        self.assertTrue(CharacterSpellSave.objects.filter(Character=char).exists())
        self.assertTrue(CharacterArcaneSpellFailCheck.objects.filter(Character=char).exists())
        self.assertTrue(CharacterMagicConditionalModifiers.objects.filter(Character=char).exists())
        self.assertTrue(CharacterSpellcasting.objects.filter(Character=char).exists())
        self.assertEqual(CharacterSkill.objects.filter(Character=char).count(), 35)


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
                'StrengthTemp': '20',
                'DexterityTemp': '',
                'ConstitutionTemp': '',
                'IntelligenceTemp': '',
                'WisdomTemp': '',
                'CharismaTemp': '',
            },
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='characterStatsForm',
        )

        self.assertEqual(resp.status_code, 200)
        self.char.characterstats.refresh_from_db()
        self.assertEqual(self.char.characterstats.Strength, 16)
        self.assertEqual(self.char.characterstats.StrengthTemp, 20)
        self.assertContains(resp, 'name="Strength"')

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
        self.assertContains(resp, 'weapon_1_Attack')


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
        self.assertContains(resp, 'Item de Protecao', count=3)


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


class CharacterSpellcastingRenderTests(TransactionTestCase):
    databases = ('default', 'sdr')

    def setUp(self):
        setup_sdr_class_table()
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

    def test_cleric_sheet_renders_domain_and_daily_spell_summary(self):
        CharacterSpellSlot.objects.create(
            Character=self.char,
            Level=1,
            SlotType='domain',
            PreparedSpellName='cure light wounds',
            IsUsed=True,
        )

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'MAGIAS')
        self.assertContains(resp, 'Dominio Healing')
        self.assertContains(resp, 'cure light wounds')
        self.assertContains(resp, 'Slots Preparados / Usados')
        self.assertContains(resp, 'Restam')

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
        self.assertContains(resp, 'characterSpellsForm')
        self.assertContains(resp, 'bless')

    def test_sorcerer_sheet_renders_known_spells_mode(self):
        self.char.Class = 'Sorcerer'
        self.char.save()
        self.char.characterstats.Charisma = 16
        self.char.characterstats.save()
        CharacterSpell.objects.create(Character=self.char, Name='magic missile', Level=1, Page='251')

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertContains(resp, 'spontaneous_known')
        self.assertContains(resp, 'magic missile')
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
        CharacterSpell.objects.create(Character=self.char, Name='custom charm', Level=1)

        self.client.force_login(self.user)
        resp = self.client.get(self.url)

        self.assertContains(resp, 'MAGIAS')
        self.assertContains(resp, 'custom')
        self.assertContains(resp, 'custom charm')


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


# ---------------------------------------------------------------------------
# Phase A — home redirect and character list filtering
# ---------------------------------------------------------------------------

class HomeRedirectTests(TestCase):

    def test_anonymous_gets_landing(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'home/landing.html')
        self.assertContains(resp, 'Entrar')

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
        self.assertTrue(self.client.login(username=ADMIN_USERNAME, password=ADMIN_PASSWORD))

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
        self.assertEqual(CharacterSkill.objects.filter(Character=char).count(), 35)
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

    def test_seed_all_is_idempotent_and_owned_by_admin(self):
        from .seeds import seed_all, seed_admin, FIGHTER_NAME, WIZARD_NAME
        first = seed_all()
        second = seed_all()
        admin = seed_admin()
        self.assertEqual(Character.objects.filter(Name=FIGHTER_NAME).count(), 1)
        self.assertEqual(Character.objects.filter(Name=WIZARD_NAME).count(), 1)
        self.assertEqual(second['fighter'].User, admin)
        self.assertEqual(second['wizard'].User, admin)
        # ids estáveis entre execuções (URLs /character/<id> não mudam)
        self.assertEqual(first['fighter'].pk, second['fighter'].pk)
        self.assertEqual(first['wizard'].pk, second['wizard'].pk)
        # rodar de novo não duplica filhos
        self.assertEqual(CharacterSkill.objects.filter(Character=second['fighter']).count(), 35)
