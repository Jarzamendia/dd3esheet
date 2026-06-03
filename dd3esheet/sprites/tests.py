from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from character.models import Character
from character.services import _bootstrap_character_siblings
from character.tests import setup_sdr_class_table
from initiative.models import Combatant, Encounter

from .models import SpriteAsset, SpriteBinding, SpriteVariant
from .seeds import seed_sprites
from .services import attach_sprites_to_combatants, sprite_for_class, sprite_for_monster


def uploaded_png(name='token.png', content=b'\x89PNG\r\n\x1a\nsprite'):
    return SimpleUploadedFile(name, content, content_type='image/png')


class ManifestDataTests(SimpleTestCase):
    def test_loads_all_assets_flat(self):
        from sprites.manifest_data import all_assets

        rows = all_assets()

        self.assertEqual(len(rows), 496)
        self.assertTrue(all('id' in row and 'type' in row for row in rows))

    def test_category_for_type(self):
        from sprites.manifest_data import category_for_type

        self.assertEqual(category_for_type('TABLETOP_TOKEN'), 'map_token')
        self.assertEqual(category_for_type('BATTLE_MAP'), 'map_tile')
        self.assertEqual(category_for_type('MAP_PIECE'), 'map_tile')
        self.assertEqual(category_for_type('CLASS_ICON'), 'class')

    def test_footprint_to_grid(self):
        from sprites.manifest_data import footprint_to_grid

        self.assertEqual(footprint_to_grid('2x2'), (2, 2))
        self.assertEqual(footprint_to_grid(None), (1, 1))


class SeedLibraryTests(TestCase):
    def test_seed_creates_all_placeholders(self):
        from django.core.management import call_command

        call_command('seed_sprite_library')

        self.assertEqual(SpriteAsset.objects.count(), 496)
        icon = SpriteAsset.objects.get(Slug='barbarian_class_icon')
        self.assertEqual(icon.Category, SpriteAsset.CLASS)
        token = SpriteAsset.objects.get(Slug='human_fighter_sword_shield')
        self.assertEqual(token.Category, SpriteAsset.MAP_TOKEN)

    def test_seed_is_idempotent(self):
        from django.core.management import call_command

        call_command('seed_sprite_library')
        call_command('seed_sprite_library')

        self.assertEqual(SpriteAsset.objects.count(), 496)

    def test_seed_sets_footprint(self):
        from django.core.management import call_command

        call_command('seed_sprite_library')

        ogre = SpriteAsset.objects.get(Slug='ogre')
        self.assertEqual((ogre.DefaultGridWidth, ogre.DefaultGridHeight), (2, 2))


class LibraryViewTests(TestCase):
    def setUp(self):
        from django.core.management import call_command

        call_command('seed_sprite_library')
        self.user = User.objects.create_user('u', password='x' * 12)
        self.client.force_login(self.user)

    def test_library_page_renders_with_theme(self):
        response = self.client.get(reverse('sprites:library'))

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('tt-themed', html)
        self.assertIn('human_fighter_sword_shield', html)

    def test_library_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('sprites:library'))

        self.assertEqual(response.status_code, 302)

    def test_asset_detail_renders_drawer_partial(self):
        response = self.client.get(reverse('sprites:asset-detail', args=['ogre']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ogre')
        self.assertContains(response, '2x2')

    def test_search_matches_slug_or_description(self):
        by_slug = self.client.get(reverse('sprites:search'), {'q': 'human_fighter_sword_shield'})
        by_description = self.client.get(reverse('sprites:search'), {'q': 'crossed greataxe'})

        self.assertEqual(by_slug.status_code, 200)
        self.assertEqual(by_description.status_code, 200)
        self.assertIn('Human Fighter Sword Shield', [row['name'] for row in by_slug.json()['sprites']])
        self.assertIn('Barbarian Class Icon', [row['name'] for row in by_description.json()['sprites']])


@override_settings(MEDIA_ROOT='/tmp/dd3esheet-test-media')
class SpriteModelTests(TestCase):
    def test_asset_generates_slug_and_checksum(self):
        asset = SpriteAsset.objects.create(
            Name='Urso Atroz',
            Category=SpriteAsset.MONSTER,
            OriginalImage=uploaded_png(),
        )

        self.assertEqual(asset.Slug, 'urso-atroz')
        self.assertGreater(asset.FileSize, 0)
        self.assertEqual(len(asset.Checksum), 64)

    def test_binding_is_unique_by_target_and_purpose(self):
        asset = SpriteAsset.objects.create(Name='Fighter', OriginalImage=uploaded_png())
        SpriteBinding.objects.create(
            TargetType=SpriteBinding.SDR_CLASS,
            TargetKey='Fighter',
            Purpose=SpriteBinding.CLASS_ICON,
            SpriteAsset=asset,
        )

        with self.assertRaises(Exception):
            SpriteBinding.objects.create(
                TargetType=SpriteBinding.SDR_CLASS,
                TargetKey='Fighter',
                Purpose=SpriteBinding.CLASS_ICON,
                SpriteAsset=asset,
            )


@override_settings(MEDIA_ROOT='/tmp/dd3esheet-test-media')
class SpriteServiceTests(TestCase):
    def test_sprite_for_class_uses_class_binding(self):
        asset = SpriteAsset.objects.create(Name='Druid Icon', OriginalImage=uploaded_png())
        SpriteBinding.objects.create(
            TargetType=SpriteBinding.SDR_CLASS,
            TargetKey='Druid',
            Purpose=SpriteBinding.CLASS_ICON,
            SpriteAsset=asset,
        )

        self.assertEqual(sprite_for_class('Druid'), asset)

    def test_sprite_for_monster_uses_monster_name_binding(self):
        asset = SpriteAsset.objects.create(Name='Brown Bear Token', OriginalImage=uploaded_png())
        SpriteBinding.objects.create(
            TargetType=SpriteBinding.SDR_MONSTER,
            TargetKey='Brown Bear',
            Purpose=SpriteBinding.MONSTER_TOKEN,
            SpriteAsset=asset,
        )

        self.assertEqual(sprite_for_monster(monster_name='Brown Bear'), asset)

    def test_attach_sprites_to_combatants_prefers_explicit_sprite_then_kind_binding(self):
        owner = User.objects.create_user(username='gm', password='pw')
        encounter = Encounter.objects.create(Owner=owner)
        explicit = SpriteAsset.objects.create(Name='Chosen Token', OriginalImage=uploaded_png('chosen.png'))
        fallback = SpriteAsset.objects.create(Name='Enemy Token', OriginalImage=uploaded_png('enemy.png'))
        SpriteBinding.objects.create(
            TargetType=SpriteBinding.COMBATANT_KIND,
            TargetKey=Combatant.ENEMY,
            Purpose=SpriteBinding.INITIATIVE_TOKEN,
            SpriteAsset=fallback,
        )
        chosen = Combatant.objects.create(
            Encounter=encounter,
            Name='Ogre',
            Kind=Combatant.ENEMY,
            SpriteAsset=explicit,
        )
        enemy = Combatant.objects.create(Encounter=encounter, Name='Goblin', Kind=Combatant.ENEMY)

        attach_sprites_to_combatants([chosen, enemy])

        self.assertIn('chosen', chosen.SpriteUrl)
        self.assertIn('enemy', enemy.SpriteUrl)


@override_settings(MEDIA_ROOT='/tmp/dd3esheet-test-media')
class SpriteManifestTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='viewer', password='pw')

    def test_manifest_requires_login(self):
        response = self.client.get(reverse('sprites:manifest'))
        self.assertEqual(response.status_code, 302)

    def test_manifest_returns_visible_sprite_urls_and_dimensions(self):
        self.client.force_login(self.user)
        asset = SpriteAsset.objects.create(
            Name='Map Token',
            Category=SpriteAsset.MAP_TOKEN,
            OriginalImage=uploaded_png('map-token.png'),
            Width=128,
            Height=128,
        )
        SpriteVariant.objects.create(
            SpriteAsset=asset,
            Variant=SpriteVariant.TOKEN_128,
            File=uploaded_png('map-token-token_128.png'),
            Width=128,
            Height=128,
        )

        response = self.client.get(
            reverse('sprites:manifest'),
            {'ids': str(asset.id), 'variant': SpriteVariant.TOKEN_128},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['sprites'][0]['id'], asset.id)
        self.assertIn('map-token-token_128', data['sprites'][0]['url'])
        self.assertEqual(data['sprites'][0]['grid']['w'], 1)
        self.assertEqual(data['sprites'][0]['grid']['h'], 1)


@override_settings(MEDIA_ROOT='/tmp/dd3esheet-test-media')
class SpriteIntegrationTests(TestCase):
    databases = {'default', 'sdr'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_sdr_class_table()

    def test_initiative_board_renders_bound_kind_sprite_image(self):
        owner = User.objects.create_user(username='gm', password='pw')
        encounter = Encounter.objects.create(Owner=owner)
        asset = SpriteAsset.objects.create(Name='Enemy Token', OriginalImage=uploaded_png('enemy.png'))
        SpriteBinding.objects.create(
            TargetType=SpriteBinding.COMBATANT_KIND,
            TargetKey=Combatant.ENEMY,
            Purpose=SpriteBinding.INITIATIVE_TOKEN,
            SpriteAsset=asset,
        )
        Combatant.objects.create(Encounter=encounter, Name='Goblin', Kind=Combatant.ENEMY)

        response = self.client.get(reverse('initiative:board-fragment', args=[encounter.Slug]))

        self.assertContains(response, 'class="init-sprite-img"')
        self.assertContains(response, 'enemy')

    def test_character_identity_renders_class_sprite_when_bound(self):
        user = User.objects.create_user(username='player', password='pw')
        character = Character.objects.create(User=user, Name='Thalara', Class='Druid', Level='9')
        _bootstrap_character_siblings(character)
        asset = SpriteAsset.objects.create(Name='Druid Icon', OriginalImage=uploaded_png('druid.png'))
        SpriteBinding.objects.create(
            TargetType=SpriteBinding.SDR_CLASS,
            TargetKey='Druid',
            Purpose=SpriteBinding.CLASS_ICON,
            SpriteAsset=asset,
        )

        self.client.force_login(user)
        response = self.client.get(reverse('character:character', args=[character.pk]))

        self.assertContains(response, 'class="brand-class-sprite"')
        self.assertContains(response, 'druid')


@override_settings(MEDIA_ROOT='/tmp/dd3esheet-test-media')
class SpriteSeedTests(TestCase):
    def test_seed_sprites_is_idempotent_and_creates_core_bindings(self):
        first = seed_sprites()
        second = seed_sprites()

        self.assertEqual(set(first), set(second))
        self.assertTrue(SpriteBinding.objects.filter(
            TargetType=SpriteBinding.SDR_CLASS,
            TargetKey='Druid',
            Purpose=SpriteBinding.CLASS_ICON,
        ).exists())
        self.assertTrue(SpriteBinding.objects.filter(
            TargetType=SpriteBinding.COMBATANT_KIND,
            TargetKey=Combatant.ENEMY,
            Purpose=SpriteBinding.INITIATIVE_TOKEN,
        ).exists())

    def test_seed_sprites_does_not_generate_image_files(self):
        seed_sprites()

        self.assertFalse(
            SpriteAsset.objects.exclude(OriginalImage='').exists()
        )
        self.assertEqual(SpriteVariant.objects.count(), 0)
