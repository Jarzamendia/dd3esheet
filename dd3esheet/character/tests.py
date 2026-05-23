from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.db import connections
from django.urls import reverse

from .models import (
    Character, CharacterStats, CharacterStatus, CharacterSavingThrows,
    CharacterAttackModifiers, CharacterSkillGraduation, CharacterOtherItemObs,
    CharacterMoney, CharacterSpellSave, CharacterArcaneSpellFailCheck,
    CharacterMagicConditionalModifiers, CharacterSkill,
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
    SDR_Class.objects.using('sdr').bulk_create(
        [SDR_Class(name=c) for c in _PHB_CORE_CLASSES]
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
