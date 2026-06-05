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

        self.assertGreater(len(rows), 496)
        self.assertTrue(all('id' in row and 'type' in row for row in rows))
        self.assertIn('scene_forest_village_editable', {row['id'] for row in rows})

    def test_category_for_type(self):
        from sprites.manifest_data import category_for_type

        self.assertEqual(category_for_type('TABLETOP_TOKEN'), 'map_token')
        self.assertEqual(category_for_type('ITEM_SPRITE'), 'item')
        self.assertEqual(category_for_type('MAP_MARKER'), 'generic')
        self.assertEqual(category_for_type('BATTLE_MAP'), 'map_tile')
        self.assertEqual(category_for_type('MAP_PIECE'), 'map_tile')
        self.assertEqual(category_for_type('CLASS_ICON'), 'class')

    def test_expansion_assets_include_placeholder_metadata(self):
        from sprites.manifest_data import all_assets

        rows = {row['id']: row for row in all_assets()}
        terrain = rows['terrain_village_dirt_road_straight']
        item = rows['item_chest_closed']

        self.assertTrue(terrain['modular'])
        self.assertEqual(terrain['state'], 'placeholder')
        self.assertEqual(terrain['subcategory'], 'village_terrain')
        self.assertEqual(terrain['expected_path'], '/sprites/original/map_tile/terrain_village_dirt_road_straight.png')
        self.assertIn('terrain_village_dirt_road_curve', terrain['variations'])
        self.assertEqual(item['category'], 'item')
        self.assertIn('item_chest_open', item['variations'])

    def test_footprint_to_grid(self):
        from sprites.manifest_data import footprint_to_grid

        self.assertEqual(footprint_to_grid('2x2'), (2, 2))
        self.assertEqual(footprint_to_grid(None), (1, 1))


class ArtConstantsTests(SimpleTestCase):
    def test_palette_has_14_colors(self):
        from sprites.manifest_data import PALETTE
        self.assertEqual(len(PALETTE), 14)
        self.assertTrue(all('hex' in c and 'name' in c for c in PALETTE))

    def test_type_specs_cover_manifest_types(self):
        from sprites.manifest_data import TYPE_SPECS
        self.assertIn('TABLETOP_TOKEN', TYPE_SPECS)
        self.assertIn('ITEM_SPRITE', TYPE_SPECS)
        self.assertIn('MAP_MARKER', TYPE_SPECS)

    def test_type_specs_carry_a_spec_blurb(self):
        from sprites.manifest_data import TYPE_SPECS
        self.assertTrue(all(t.get('spec') for t in TYPE_SPECS.values()))

    def test_footprint_feet(self):
        from sprites.manifest_data import footprint_feet
        self.assertEqual(footprint_feet('2x2'), '10×10 ft')
        self.assertIsNone(footprint_feet(None))


class SeedLibraryTests(TestCase):
    def test_seed_creates_all_placeholders(self):
        from django.core.management import call_command
        from sprites.manifest_data import all_assets

        call_command('seed_sprite_library')

        self.assertEqual(SpriteAsset.objects.count(), len(all_assets()))
        icon = SpriteAsset.objects.get(Slug='barbarian_class_icon')
        self.assertEqual(icon.Category, SpriteAsset.CLASS)
        token = SpriteAsset.objects.get(Slug='human_fighter_sword_shield')
        self.assertEqual(token.Category, SpriteAsset.MAP_TOKEN)

    def test_seed_is_idempotent(self):
        from django.core.management import call_command
        from sprites.manifest_data import all_assets

        call_command('seed_sprite_library')
        call_command('seed_sprite_library')

        self.assertEqual(SpriteAsset.objects.count(), len(all_assets()))

    def test_seed_sets_footprint(self):
        from django.core.management import call_command

        call_command('seed_sprite_library')

        ogre = SpriteAsset.objects.get(Slug='ogre')
        self.assertEqual((ogre.DefaultGridWidth, ogre.DefaultGridHeight), (2, 2))

    def test_seed_creates_tokens_plan_placeholders(self):
        from django.core.management import call_command

        call_command('seed_sprite_library')

        terrain = SpriteAsset.objects.get(Slug='terrain_village_dirt_road_straight')
        scene = SpriteAsset.objects.get(Slug='scene_forest_village_editable')
        item = SpriteAsset.objects.get(Slug='item_chest_closed')
        marker = SpriteAsset.objects.get(Slug='marker_danger')

        self.assertEqual(terrain.Category, SpriteAsset.MAP_TILE)
        self.assertEqual((terrain.DefaultGridWidth, terrain.DefaultGridHeight), (2, 1))
        self.assertEqual(scene.Category, SpriteAsset.MAP_TILE)
        self.assertEqual(item.Category, SpriteAsset.ITEM)
        self.assertEqual(marker.Category, SpriteAsset.GENERIC)
        self.assertFalse(SpriteAsset.objects.exclude(OriginalImage='').exists())


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


class ArtSpecViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('a', password='x' * 12)
        self.client.force_login(self.user)

    def test_spec_page_is_data_driven(self):
        resp = self.client.get(reverse('sprites:art-spec'))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('tt-themed', html)       # tema (fatia A)
        self.assertIn('#c8923a', html)         # paleta (ochre) renderizada
        self.assertIn('Tabletop Token', html)  # spec de tipo renderizada

    def test_spec_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('sprites:art-spec')).status_code, 302)


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


class TerrainKindManifestTests(SimpleTestCase):
    def _map_pieces(self):
        from .manifest_data import all_assets
        return [a for a in all_assets() if a.get('type') == 'MAP_PIECE']

    def test_every_map_piece_has_valid_terrain_kind(self):
        missing = [a['id'] for a in self._map_pieces()
                   if a.get('terrain_kind') not in ('base', 'detail')]
        self.assertEqual(missing, [], f'map pieces sem terrain_kind valido: {missing}')

    def test_known_base_and_detail_examples(self):
        kinds = {a['id']: a.get('terrain_kind') for a in self._map_pieces()}
        self.assertEqual(kinds.get('grass_field_tile'), 'base')
        self.assertEqual(kinds.get('dungeon_floor_tile'), 'base')
        self.assertEqual(kinds.get('terrain_swamp_mud_tile'), 'base')
        self.assertEqual(kinds.get('dirt_road_straight'), 'detail')
        self.assertEqual(kinds.get('river_segment'), 'detail')
        self.assertEqual(kinds.get('terrain_village_fence_gate'), 'detail')

    def test_terrain_kind_by_slug_helper(self):
        from .manifest_data import terrain_kind_by_slug
        mapping = terrain_kind_by_slug()
        self.assertEqual(mapping['grass_field_tile'], 'base')
        self.assertEqual(mapping['dirt_road_straight'], 'detail')
        self.assertNotIn('barbarian_class_icon', mapping)
        ids = {a['id'] for a in self._map_pieces()}
        self.assertEqual(set(mapping), ids)
