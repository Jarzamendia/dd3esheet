You are Claude Design generating a complete, cohesive sprite library for a D&D 3.5 virtual tabletop and character sheet web app.

Generate production-ready raster assets only. Every asset must look like it belongs to the same hand-inked fantasy sourcebook set. Follow the fixed art direction, technical specifications, and asset manifest below. Do not add explanations, labels, captions, UI, frames, watermarks, signatures, borders, grids, or text inside any image.

STYLE

Use a warm parchment storybook style: digital illustration that looks hand-inked for a classic fantasy tabletop RPG sourcebook. Use confident dark ink outlines of even medium weight, semi-flat cel shading with 2 or 3 tonal steps per color, subtle aged-paper grain, and soft overhead lighting. Keep the mood heroic, readable, friendly, and timeless.

Use this palette family across the whole set: dark ink #2b2622, parchment #efe6d2, ochre #c8923a, leather #7a4f2a, forest green #4f6b3a, iron #6b6f73, deep red #8a2f28, steel blue #3f6079, bone #d6c6aa, shadow brown #493628, muted gold #b58a36, arcane teal #2f6f6a, royal blue #314f7c, and dull violet #5d4978. Use moderate saturation. Avoid neon colors, pastel colors, oversaturated effects, photo realism, airbrushed realism, plastic 3D rendering, modern sci-fi details, lens flare, dramatic rim light, and cluttered backgrounds.

GLOBAL OUTPUT RULES

Create each listed asset as a separate file. Use lowercase snake_case file names matching the asset id. Transparent assets must be PNG with alpha. Opaque map assets may be PNG or high-quality WebP. Keep the subject readable at small tabletop sizes. Do not crop important anatomy, weapons, silhouettes, or props. Do not draw token rings, base discs, UI frames, health bars, selection marks, grid lines, labels, letters, numbers, or symbols that look like UI.

ASSET TYPE SPECIFICATIONS

TABLETOP_TOKEN:
Canvas 512x512 px. Transparent PNG. Top-down high-angle view, about 60 degrees from the table, like a painted miniature on a virtual battle map. One subject only, centered, facing generally upward toward the camera, neutral or lightly dynamic pose. Circle-safe composition: all important details must fit inside the central inscribed circle because the app may crop tokens into circles. Leave the four corners empty. Add only a small soft elliptical contact shadow under the subject, kept inside the circle. No base ring. Use the listed footprint only as metadata: the art canvas remains 512x512 for every creature size.

PROP_TOKEN:
Canvas 512x512 px. Transparent PNG. Top-down view. One object or terrain prop only, centered, with a small contact shadow. Circle-safe unless the object is intentionally rectangular. Use the listed footprint as app metadata; the art canvas remains 512x512.

STATUS_MARKER:
Canvas 256x256 px. Transparent PNG. Simple readable pictogram or small magical effect, no text, no letters, no numbers. It must read clearly at 32x32 px.

CLASS_ICON:
Canvas 512x512 px. Transparent PNG. Emblem-like class object or silhouette, not a UI button and not inside a border. Centered and readable at 96x96 px. No text.

PORTRAIT:
Canvas 640x640 px. Opaque parchment-friendly background. Bust or waist-up character portrait in the same inked storybook style. No text, no frame, no border.

BATTLE_MAP:
Canvas 2048x1536 px unless noted otherwise. Fully opaque, full bleed. Straight top-down view. Designed on a 64 px grid scale where one grid cell equals 5 feet, but do not draw grid lines. Lay out walls, floors, terrain, furniture, doors, and obstacles so they align naturally to the invisible grid. No tokens, no characters, no labels, no text.

CITY_OR_WORLD_MAP:
Canvas 2048x1536 px. Fully opaque, full bleed. Illustrated top-down cartography on aged parchment with roads, rivers, forests, hills, walls, districts, coastlines, or landmarks as requested. Label-free: no place names, no text, no compass text.

MAP_PIECE:
Canvas 512x512 px. Transparent PNG. Straight top-down view of one reusable map piece designed to tile on the virtual tabletop's pointy-top hexagonal battle grid (odd-r offset, one hex equals 5 feet). Each piece is a single modular building block - a floor patch, wall run, corridor, doorway, stairs, water, chasm edge, road, or natural feature - that a master can place repeatedly and butt against neighboring pieces to assemble a full scene from parts. Align edges to the hex lattice and keep straight architectural edges parallel to a hex row so adjacent pieces abut without visible seams. Unlike tokens, map pieces are NOT circle-safe: they are meant to fill and tile their hex footprint edge to edge. Use the listed footprint, counted in hexes, as app metadata; the art canvas stays 512x512. Add only a faint contact shadow under raised features (walls, rubble, stairs); flat ground pieces need no shadow. No drawn grid lines, no base ring, no tokens, no text.

SPRITE SIZE AND FOOTPRINT RULES

Tiny, Small, and Medium creatures: 512x512 transparent token, app footprint 1x1.
Long Medium mounts or furniture may use app footprint 2x1 or 1x2 while still using a 512x512 transparent canvas.
Large creatures: 512x512 transparent token, app footprint 2x2.
Huge creatures: 512x512 transparent token, app footprint 3x3.
Gargantuan creatures: 512x512 transparent token, app footprint 4x4.
Colossal creatures: 512x512 transparent token, app footprint 6x6.
Small props: 512x512 transparent token, app footprint 1x1.
Wide props: 512x512 transparent token, app footprint 2x1.
Tall props: 512x512 transparent token, app footprint 1x2.
Large set pieces: 512x512 transparent token, app footprint 2x2, 3x3, or 4x4 as listed.
Map pieces: 512x512 transparent token; footprint counted in pointy-top hexes (1x1, 2x1, 2x2, etc.) and designed to tile seamlessly against neighbors rather than be circle-safe.

ASSET MANIFEST

CLASS ICONS

- barbarian_class_icon: CLASS_ICON, 512x512 transparent PNG, crossed greataxe and fur mantle motif.
- bard_class_icon: CLASS_ICON, 512x512 transparent PNG, lute, rapier, and ribbon motif.
- cleric_class_icon: CLASS_ICON, 512x512 transparent PNG, mace, holy symbol, and sunburst motif.
- druid_class_icon: CLASS_ICON, 512x512 transparent PNG, oak leaf, staff, and crescent motif.
- fighter_class_icon: CLASS_ICON, 512x512 transparent PNG, sword, shield, and worn helm motif.
- monk_class_icon: CLASS_ICON, 512x512 transparent PNG, open hand, prayer beads, and simple staff motif.
- paladin_class_icon: CLASS_ICON, 512x512 transparent PNG, polished shield, longsword, and radiant oath motif.
- ranger_class_icon: CLASS_ICON, 512x512 transparent PNG, longbow, trail marker, and leaf motif.
- rogue_class_icon: CLASS_ICON, 512x512 transparent PNG, dagger, lockpick, and hood motif.
- sorcerer_class_icon: CLASS_ICON, 512x512 transparent PNG, raw arcane flame around a hand motif.
- wizard_class_icon: CLASS_ICON, 512x512 transparent PNG, spellbook, wand, and star diagram motif.

CLASS PORTRAITS

- barbarian_class_portrait: PORTRAIT, 640x640 opaque PNG, rugged warrior with furs and greataxe.
- bard_class_portrait: PORTRAIT, 640x640 opaque PNG, charming performer with lute and rapier.
- cleric_class_portrait: PORTRAIT, 640x640 opaque PNG, armored priest with holy symbol and mace.
- druid_class_portrait: PORTRAIT, 640x640 opaque PNG, forest mystic with staff and leaf cloak.
- fighter_class_portrait: PORTRAIT, 640x640 opaque PNG, disciplined armored veteran with shield.
- monk_class_portrait: PORTRAIT, 640x640 opaque PNG, calm martial artist with simple robes.
- paladin_class_portrait: PORTRAIT, 640x640 opaque PNG, noble holy knight with bright shield.
- ranger_class_portrait: PORTRAIT, 640x640 opaque PNG, weathered archer with green cloak.
- rogue_class_portrait: PORTRAIT, 640x640 opaque PNG, alert infiltrator with hood and daggers.
- sorcerer_class_portrait: PORTRAIT, 640x640 opaque PNG, innate spellcaster with subtle arcane aura.
- wizard_class_portrait: PORTRAIT, 640x640 opaque PNG, scholar mage with spellbook and wand.

PLAYER CHARACTER TOKENS

- human_fighter_sword_shield: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, human fighter with longsword and shield.
- human_fighter_greatsword: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, human fighter in chainmail with greatsword.
- dwarf_cleric_warpriest: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, dwarf cleric with mace and shield.
- dwarf_fighter_axe: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, dwarf warrior with battleaxe.
- elf_wizard_evoker: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, elf wizard with robe, wand, and spellbook.
- elf_ranger_archer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, elf ranger with longbow and cloak.
- halfling_rogue_daggers: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, halfling rogue with twin daggers.
- halfling_bard_lute: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, halfling bard with lute and rapier.
- gnome_illusionist: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, gnome wizard illusionist with bright scarf.
- gnome_bard_wanderer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, gnome bard with small drum and dagger.
- half_elf_ranger_dual_blades: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, half-elf ranger with two short swords.
- half_elf_sorcerer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, half-elf sorcerer with arcane hand gesture.
- half_orc_barbarian_greataxe: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, half-orc barbarian with greataxe and fur cloak.
- half_orc_fighter_polearm: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, half-orc fighter with polearm.
- human_paladin_longsword: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, human paladin with longsword and shield.
- human_cleric_healer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, human cleric with staff and holy symbol.
- human_monk_unarmed: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, human monk in ready stance.
- human_rogue_crossbow: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, human rogue with hand crossbow.
- human_sorcerer_draconic: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, human sorcerer with draconic cloak motif.
- human_wizard_abjurer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, human wizard with protective magic gesture.
- elf_druid_staff: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, elf druid with staff and leaf mantle.
- dwarf_paladin_hammer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, dwarf paladin with warhammer and shield.
- halfling_ranger_sling: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, halfling ranger with sling and shortbow.
- gnome_cleric_trickster: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, gnome cleric with small mace and holy charm.

COMPANION AND FAMILIAR TOKENS

- riding_horse: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, saddled horse top-down.
- warhorse_light: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, armored light warhorse.
- warhorse_heavy: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, armored heavy warhorse.
- pony: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, saddled pony.
- mule_pack: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, pack mule with saddlebags.
- riding_dog: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, armored riding dog.
- hawk_familiar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, hawk with wings tucked enough to stay circle-safe.
- owl_familiar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, owl familiar.
- raven_familiar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, raven familiar.
- cat_familiar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, alert black cat familiar.
- rat_familiar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small rat familiar.
- toad_familiar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, squat toad familiar.
- weasel_familiar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, slender weasel familiar.
- snake_familiar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, coiled viper familiar.
- wolf_companion: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, loyal wolf animal companion.
- black_bear_companion: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, black bear animal companion.
- brown_bear_companion: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, brown bear animal companion.
- dire_wolf_companion: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, dire wolf animal companion.
- eagle_companion: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, eagle animal companion.
- leopard_companion: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, leopard animal companion.

NPC TOKENS

- village_commoner: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, plain villager with simple tools.
- farmer_pitchfork: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, farmer with pitchfork.
- tavern_keeper: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, tavern keeper with apron and mug.
- merchant_trader: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, traveling merchant with satchel.
- noble_courtier: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, noble in rich but muted clothing.
- city_guard_spear: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, city guard with spear and shield.
- veteran_sergeant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, veteran guard captain with tabard.
- priest_temple: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, temple priest with staff.
- acolyte_young: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, young acolyte with candle.
- sage_scholar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, old scholar with scrolls.
- apprentice_mage: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, apprentice spellcaster with wand.
- blacksmith: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, blacksmith with hammer and apron.
- healer_herbalist: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, herbalist with satchel and herbs.
- inn_server: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, inn server with tray.
- bard_traveler: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, traveling bard with lute.
- thief_cutpurse: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, street thief with cloak.
- assassin_hooded: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, hooded assassin with dagger.
- cultist_robed: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, robed cultist with ritual dagger.
- bandit_knife: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, rough bandit with knife.
- bandit_archer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, bandit archer with shortbow.
- pirate_cutlass: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, pirate with cutlass.
- caravan_guard: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, armored caravan guard.
- prisoner_shackled: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, shackled prisoner.
- child_villager: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small village child, non-threatening.
- ghostly_ancestor: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, translucent ancestral spirit in the same inked style, subtle and not glowing heavily.

HUMANOID ENEMY TOKENS

- goblin_skirmisher: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, goblin with rusty scimitar and crude shield.
- goblin_archer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, goblin with shortbow.
- goblin_shaman: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, goblin shaman with bone charms.
- kobold_spearman: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, kobold with spear and small shield.
- kobold_slinger: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, kobold with sling and pouch.
- kobold_trapmaker: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, kobold with tools and wire.
- orc_raider: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, orc with greataxe.
- orc_archer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, orc with crude longbow.
- orc_war_chief: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, armored orc leader with axe.
- hobgoblin_soldier: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, disciplined hobgoblin with sword and shield.
- hobgoblin_captain: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, hobgoblin officer with banner spear.
- bugbear_brute: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, hulking bugbear with morningstar.
- gnoll_hunter: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, hyena-headed gnoll with spear.
- gnoll_pack_lord: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, stronger gnoll with battleaxe.
- lizardfolk_warrior: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, lizardfolk with club and shield.
- troglodyte_savage: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, troglodyte with stone axe.
- sahuagin_raider: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, aquatic sahuagin with trident.
- kuo_toa_monitor: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, fishlike underground warrior with spear.
- drow_scout: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, dark elf scout with hand crossbow.
- drow_priestess: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, drow priestess with mace and cloak.
- duergar_warrior: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, gray dwarf warrior with warhammer.
- derro_madcap: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, derro with hooked blade.
- grimlock_cavern_hunter: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, blind cavern humanoid with stone club.

UNDEAD TOKENS

- skeleton_warrior: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, armed skeleton with round shield.
- skeleton_archer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, skeleton with shortbow.
- zombie_commoner: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, shambling zombie.
- ghoul: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, crouched ghoul with claws.
- ghast: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, stronger ghoul-like undead.
- wight: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, armored wight with dead eyes.
- shadow_undead: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, smoky shadow figure, readable silhouette.
- wraith: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, hooded spectral undead, subtle transparency.
- mummy: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, bandaged mummy with ancient jewelry.
- vampire_spawn: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, elegant feral vampire spawn.
- vampire_lord: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, aristocratic vampire with cloak.
- lich: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, skeletal archmage with tattered robes.
- allip: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, indistinct spectral mad spirit.
- bodak: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, gaunt undead with unsettling stare.
- mohrg: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, skeletal undead with extended tongue, not too grotesque.

BEAST AND VERMIN TOKENS

- wolf: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, gray wolf.
- dire_wolf: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, massive dire wolf.
- dog_guard: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, guard dog.
- black_bear: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, black bear.
- brown_bear: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, brown bear.
- dire_bear: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, huge dire bear.
- boar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, wild boar.
- dire_boar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, dire boar.
- lion: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, lion.
- tiger: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, tiger.
- leopard: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, leopard.
- rat_swarm: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, mass of small rats, readable as swarm.
- bat_swarm: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, cluster of bats, circle-safe.
- giant_rat: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, oversized rat.
- giant_centipede: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, coiled enough to fit.
- giant_spider_medium: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, giant spider.
- giant_spider_large: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, large giant spider.
- monstrous_scorpion_medium: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, monstrous scorpion.
- monstrous_scorpion_large: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, large monstrous scorpion.
- giant_wasp: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, giant wasp with wings kept inside circle.
- giant_praying_mantis: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, giant mantis.
- crocodile: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, crocodile top-down.
- shark: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, shark top-down.
- constrictor_snake: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, coiled constrictor snake.
- viper_snake: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, coiled venomous snake.

GIANT AND MONSTROUS HUMANOID TOKENS

- ogre: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, ogre with greatclub.
- ogre_mage: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, horned ogre mage with curved blade.
- troll: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, long-limbed troll with claws.
- hill_giant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, crude hill giant with club.
- stone_giant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, lean stone giant with rock.
- frost_giant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, frost giant warrior with axe.
- fire_giant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, armored fire giant with sword.
- ettin: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, two-headed giant brute.
- minotaur: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, minotaur with greataxe.
- centaur_archer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, centaur with longbow.
- harpy: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, harpy with folded wings.
- gargoyle: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, crouched stone gargoyle.
- medusa: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, snake-haired archer.
- yuan_ti_pureblood: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, subtle serpent humanoid.
- yuan_ti_abomination: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, serpentine monster.

ABERRATION TOKENS

- beholder_like_eye_tyrant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, floating many-eyed orb monster, generic fantasy eye tyrant, no copied trademarked exact design.
- carrion_crawler: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, tentacled carrion crawler.
- chuul: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, lobster-like aberration with tentacles.
- cloaker: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, manta-like cloaker with tail.
- ettercap: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, spiderlike humanoid.
- gibbering_mouther: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, amorphous many-mouthed aberration, stylized not graphic.
- grick: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, wormlike ambush predator with tentacle head.
- mimic_chest: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, treasure chest mimic with teeth and tongue.
- mind_flayer_like_psion: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, robed tentacled psionic humanoid, generic and not copied from any single published image.
- otyugh: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, three-legged refuse monster with tentacles.
- rust_monster: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, insectoid rust monster with feathery antennae.
- umber_hulk: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, burrowing insectoid brute.

DRAGON TOKENS

- dragon_wyrmling_red: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small red dragon wyrmling.
- dragon_wyrmling_black: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small black dragon wyrmling.
- dragon_wyrmling_green: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small green dragon wyrmling.
- dragon_young_red: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 4x4, young red dragon coiled circle-safe.
- dragon_young_blue: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 4x4, young blue dragon with folded wings.
- dragon_young_green: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 4x4, young green dragon with folded wings.
- dragon_young_black: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 4x4, young black dragon with horns.
- dragon_young_white: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 4x4, young white dragon with icy spines.
- dragon_adult_red: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 6x6, adult red dragon coiled tightly to fit canvas.
- dragon_adult_gold: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 6x6, adult gold dragon with folded wings.
- wyvern: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, wyvern with stinger tail.
- pseudodragon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, tiny pseudodragon familiar.

ELEMENTAL AND OUTSIDER TOKENS

- air_elemental_medium: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, swirling air form with readable silhouette.
- air_elemental_large: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, larger air elemental.
- earth_elemental_medium: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, rocky humanoid.
- earth_elemental_large: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, large rocky humanoid.
- fire_elemental_medium: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, living flame, warm inked style, not neon.
- fire_elemental_large: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, large living flame.
- water_elemental_medium: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, wave-shaped humanoid.
- water_elemental_large: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, large wave-shaped humanoid.
- celestial_lantern_archon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small floating celestial orb with subtle wings, no harsh glow.
- hound_archon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, dog-headed celestial warrior.
- avoral_guardinal: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, winged avian celestial.
- imp_familiar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, tiny imp with folded wings.
- quasit: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, tiny demonic familiar.
- lemure: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, shapeless low fiend, not graphic.
- dretch: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, squat demon.
- hell_hound: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, infernal hound with ember markings.
- barbed_devil: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, spined devil warrior.
- chain_devil: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, chain-wrapped devil, no graphic gore.
- erinyes_archer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, winged fiend archer.
- succubus_tempter: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, winged fiend spellcaster, tasteful fantasy design.

CONSTRUCT AND OOZE TOKENS

- animated_armor: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, empty animated armor with sword.
- animated_table: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, animated wooden table.
- animated_statue: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, stone statue construct.
- homunculus: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, tiny alchemical construct.
- shield_guardian: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, bulky shield-bearing guardian construct.
- stone_golem: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, carved stone golem.
- iron_golem: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, heavy iron golem.
- flesh_golem: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, stitched construct, stylized not graphic.
- gelatinous_cube: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, translucent cube with subtle internal debris.
- gray_ooze: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, flat gray ooze puddle.
- ochre_jelly: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, yellow-brown jelly mass.
- black_pudding: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, dark viscous ooze.

PLANT AND FEY TOKENS

- dryad: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, tree spirit humanoid.
- pixie: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, tiny winged fey, wings inside circle.
- satyr: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, goat-legged fey with pipes.
- nymph: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, graceful fey guardian, tasteful.
- treant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, walking ancient tree.
- assassin_vine: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, grasping vine mass.
- shambling_mound: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, walking swamp vegetation.
- violet_fungus: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, cluster of violet fungus stalks.
- shrieker_fungus: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, pale mushroom cluster.

SWARM AND SUMMONING TOKENS

- celestial_eagle_summon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, celestial-marked eagle.
- fiendish_wolf_summon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, fiendish-marked wolf.
- celestial_bison_summon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, celestial bison.
- fiendish_giant_spider_summon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, fiendish giant spider.
- small_fire_summon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, minor fire creature.
- small_earth_summon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, minor earth creature.
- insect_swarm: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, dense swarm cloud, circle-safe.
- spider_swarm: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, many small spiders, not graphic.
- centipede_swarm: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, centipede swarm, readable.

MAGICAL BEAST TOKENS

- owlbear: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, bear-owl hybrid with hooked beak and claws.
- griffon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, eagle-lion griffon, wings folded circle-safe.
- hippogriff: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, horse-eagle hippogriff, wings tucked.
- pegasus: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, winged horse with wings tucked inside circle.
- unicorn: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, noble horned unicorn.
- worg: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, large evil wolf, worg.
- winter_wolf: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, white frost wolf.
- blink_dog: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, tan teleporting hound.
- displacer_beast: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, six-legged panther with two tentacles.
- bulette: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, armored land-shark burrower.
- ankheg: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, insectoid burrower with mandibles.
- basilisk: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, eight-legged reptile.
- cockatrice: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, rooster-lizard cockatrice.
- chimera: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, lion-goat-dragon three-headed beast.
- manticore: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, lion body, bat wings, spiked tail.
- hydra_five_head: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, five-headed reptilian hydra.
- gorgon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, iron-plated bull.
- behir: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, many-legged serpentine beast, coiled circle-safe.
- sea_cat: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, finned lion-fish predator.
- gynosphinx: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, winged lion with a woman's head.
- phase_spider: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, large violet phase spider.
- girallon: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, four-armed white ape.
- choker: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small grasping aberration with long arms.
- darkmantle: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, cave-clinging mantle creature.

ADDITIONAL ANIMAL AND VERMIN TOKENS

- elephant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, tusked elephant.
- camel: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, saddled or wild camel.
- rhinoceros: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, horned rhinoceros.
- ape: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, great ape.
- dire_badger: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, oversized dire badger.
- monitor_lizard: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, large monitor lizard.
- giant_frog: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, oversized frog.
- giant_ant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, soldier giant ant.

ADDITIONAL UNDEAD TOKENS

- spectre: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, gaunt spectral undead, subtle transparency.
- ghost_apparition: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, translucent ghost, readable silhouette.
- dread_wraith: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, large hooded wraith, subtle transparency.
- devourer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, gaunt undead with a trapped spirit in its ribcage.
- skeletal_horse: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x1, undead skeletal steed.
- zombie_dog: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, shambling undead hound.

ADDITIONAL GIANT TOKENS

- cloud_giant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, regal cloud giant with morningstar.
- storm_giant: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, violet-skinned storm giant with greatsword.
- cyclops: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, one-eyed cyclops with club.
- fomorian: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, misshapen fomorian giant.

ADDITIONAL OUTSIDER TOKENS

- balor: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, winged flaming demon lord with sword and whip.
- marilith: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, six-armed serpent-bodied demon.
- vrock: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, vulture-headed demon.
- hezrou: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, toad-like demon brute.
- glabrezu: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, dog-headed pincered demon.
- bone_devil: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, skeletal scorpion-tailed devil.
- pit_fiend: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, winged armored arch-devil.
- planetar: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, green-skinned winged celestial with greatsword.

ADDITIONAL ABERRATION TOKENS

- aboleth: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, huge fish-like aberration with tentacles.
- roper: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, stalagmite-shaped predator with tendrils.
- will_o_wisp: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, floating eerie light orb, subtle glow.
- drider: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, dark elf torso on a spider body.
- grell: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, floating brain-shaped aberration with beak and tentacles.

ADDITIONAL CONSTRUCT TOKENS

- clay_golem: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 2x2, crude clay humanoid golem.
- retriever: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, four-legged spider-like construct.
- animated_object_generic: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, generic animated object with faint runes.

ADDITIONAL DRAGON TOKENS

- dragon_wyrmling_white: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small white dragon wyrmling with icy spines.
- dragon_wyrmling_blue: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small blue dragon wyrmling with horn.
- dragon_wyrmling_brass: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small brass dragon wyrmling.
- dragon_wyrmling_bronze: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small bronze dragon wyrmling.
- dragon_wyrmling_copper: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small copper dragon wyrmling.
- dragon_wyrmling_silver: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, small silver dragon wyrmling.
- dragon_turtle: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 3x3, huge armored dragon turtle.

ADDITIONAL NPC TOKENS

- mayor_burgomaster: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, town mayor in chain of office.
- town_crier: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, crier with handbell.
- fisherman: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, fisher with net and basket.
- hunter_trapper: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, hunter with bow and pelts.
- gravedigger: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, gravedigger with shovel.
- jailer: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, burly jailer with key ring.
- man_at_arms: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, armored soldier with sword.
- court_wizard: TABLETOP_TOKEN, 512x512 transparent PNG, footprint 1x1, robed advisor mage with staff.

PROP TOKENS: DUNGEON, TAVERN, AND TOWN

- wooden_door_closed: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, closed wooden door top-down.
- wooden_door_open: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, open wooden door top-down.
- iron_door_closed: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, closed iron door.
- portcullis: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, iron portcullis.
- stone_pillar_intact: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, intact stone pillar.
- stone_pillar_broken: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, broken stone pillar.
- rubble_pile: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, dungeon rubble.
- large_rubble_field: PROP_TOKEN, 512x512 transparent PNG, footprint 2x2, larger rubble.
- treasure_chest_closed: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, closed treasure chest.
- treasure_chest_open: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, open treasure chest with coins.
- locked_strongbox: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, iron strongbox.
- barrel: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, wooden barrel.
- crate: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, wooden crate.
- crate_stack: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, stacked crates.
- sack_pile: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, sacks of grain.
- table_round: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, round tavern table.
- table_long: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, long wooden table.
- bench: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, wooden bench.
- chair: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, simple chair.
- bed_simple: PROP_TOKEN, 512x512 transparent PNG, footprint 1x2, simple bed.
- bookshelf: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, top-down bookshelf.
- altar_stone: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, stone altar.
- statue_knight: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, knight statue.
- statue_dragon: PROP_TOKEN, 512x512 transparent PNG, footprint 2x2, dragon statue.
- brazier_lit: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, lit brazier, controlled warm flame.
- brazier_unlit: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, unlit brazier.
- campfire_lit: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, small campfire.
- torch_wall: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, wall torch angled top-down.
- fountain_round: PROP_TOKEN, 512x512 transparent PNG, footprint 2x2, round stone fountain.
- well_stone: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, stone well.
- wagon: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, wooden wagon.
- cart_hand: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, small handcart.
- market_stall: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, canvas market stall.
- anvil: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, blacksmith anvil.
- weapon_rack: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, weapon rack.
- armor_stand: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, armor stand.
- hay_bale: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, hay bale.
- ladder: PROP_TOKEN, 512x512 transparent PNG, footprint 1x2, ladder top-down.
- rope_coil: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, coil of rope.
- magic_circle: PROP_TOKEN, 512x512 transparent PNG, footprint 2x2, chalk ritual circle with abstract marks only, no readable text.
- bloodless_ritual_altar: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, ominous altar without gore.
- sarcophagus_closed: PROP_TOKEN, 512x512 transparent PNG, footprint 1x2, closed stone sarcophagus.
- sarcophagus_open: PROP_TOKEN, 512x512 transparent PNG, footprint 1x2, open sarcophagus.
- gravestone: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, blank gravestone, no text.
- bone_pile: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, old bones, not graphic.
- puddle_water: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, water puddle.
- puddle_slime: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, greenish slime puddle.

PROP TOKENS: WILDERNESS AND TERRAIN

- tree_oak: PROP_TOKEN, 512x512 transparent PNG, footprint 2x2, top-down oak tree canopy.
- tree_pine: PROP_TOKEN, 512x512 transparent PNG, footprint 2x2, top-down pine tree.
- tree_dead: PROP_TOKEN, 512x512 transparent PNG, footprint 2x2, dead tree.
- bush: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, dense bush.
- brambles: PROP_TOKEN, 512x512 transparent PNG, footprint 2x2, thorny bramble patch.
- boulder_small: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, small boulder.
- boulder_large: PROP_TOKEN, 512x512 transparent PNG, footprint 2x2, large boulder.
- fallen_log: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, fallen log.
- stump: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, tree stump.
- mushrooms_cluster: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, fantasy mushroom cluster.
- shallow_stream_piece: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, transparent-edged stream segment.
- bridge_wooden: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, wooden bridge.
- cliff_edge: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, rocky cliff edge piece.
- cave_stalagmites: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, stalagmite cluster.
- cave_crystals: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, muted cave crystals.
- snow_drift: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, snow drift.
- desert_rock: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, desert rock.
- swamp_reeds: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, swamp reeds.
- lava_crack: PROP_TOKEN, 512x512 transparent PNG, footprint 2x1, cracked stone with muted lava glow.

MARKER AND STATUS SPRITES

- party_banner_marker: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, small blank party banner marker, no emblem text.
- you_are_here_pin: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, parchment map pin marker, no text.
- destination_flag_marker: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, small blank destination flag.
- trap_marker_generic: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, subtle spiked trap marker, no symbol text.
- secret_door_marker: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, subtle cracked wall marker.
- area_target_marker: STATUS_MARKER, 256x256 transparent PNG, circular target-like magic mark with no text.
- condition_blinded: STATUS_MARKER, 256x256 transparent PNG, closed eye pictogram.
- condition_deafened: STATUS_MARKER, 256x256 transparent PNG, muted ear pictogram, no slash text.
- condition_stunned: STATUS_MARKER, 256x256 transparent PNG, dazed star swirl pictogram.
- condition_prone: STATUS_MARKER, 256x256 transparent PNG, fallen figure pictogram.
- condition_grappled: STATUS_MARKER, 256x256 transparent PNG, binding rope pictogram.
- condition_poisoned: STATUS_MARKER, 256x256 transparent PNG, green vial pictogram.
- condition_diseased: STATUS_MARKER, 256x256 transparent PNG, sickly blot pictogram.
- condition_frightened: STATUS_MARKER, 256x256 transparent PNG, trembling mask pictogram.
- condition_invisible: STATUS_MARKER, 256x256 transparent PNG, fading silhouette pictogram.
- condition_flying: STATUS_MARKER, 256x256 transparent PNG, wing pictogram.
- condition_hasted: STATUS_MARKER, 256x256 transparent PNG, swift boot pictogram.
- condition_slowed: STATUS_MARKER, 256x256 transparent PNG, heavy boot pictogram.
- condition_blessed: STATUS_MARKER, 256x256 transparent PNG, warm sunburst pictogram.
- condition_cursed: STATUS_MARKER, 256x256 transparent PNG, cracked black charm pictogram.
- spell_area_burst: STATUS_MARKER, 256x256 transparent PNG, soft circular burst template marker, no numbers.
- spell_area_cone: STATUS_MARKER, 256x256 transparent PNG, cone area marker pictogram.
- spell_area_line: STATUS_MARKER, 256x256 transparent PNG, straight line area marker pictogram.

ITEM SPRITES

- longsword_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, single longsword.
- greatsword_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, single greatsword.
- battleaxe_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, battleaxe.
- greataxe_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, greataxe.
- mace_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, heavy mace.
- warhammer_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, warhammer.
- spear_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, spear angled within circle.
- longbow_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, longbow and arrow.
- crossbow_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, light crossbow.
- dagger_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, dagger.
- shield_wood_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, wooden shield.
- shield_steel_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, steel shield.
- chainmail_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, folded chainmail.
- plate_armor_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, plate armor torso.
- potion_red_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, red potion vial.
- potion_blue_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, blue potion vial.
- scroll_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, rolled parchment scroll, no text.
- spellbook_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, closed spellbook with blank cover.
- wand_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, slender wand.
- staff_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, quarterstaff.
- ring_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, simple magic ring.
- amulet_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, amulet.
- coin_pouch_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, coin pouch.
- gem_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, cut gem.
- key_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, old iron key.
- thieves_tools_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, lockpick tools.
- holy_symbol_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, generic holy symbol, no specific real-world symbol and no text.
- rations_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, trail rations.
- lantern_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, hooded lantern.
- backpack_item: PROP_TOKEN, 512x512 transparent PNG, footprint 1x1, adventurer backpack.

BATTLE MAPS

- stone_dungeon_room: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, stone chamber, broken pillars, rubble, central dais, no grid.
- dungeon_crossroads: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, four-way corridor junction with alcoves, no grid.
- dungeon_prison_block: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, cells, barred doors, guard room, no grid.
- dungeon_trap_hall: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, long hall with pressure plates and side niches, no grid and no labels.
- crypt_chamber: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, sarcophagi, cracked stone, altar, no grid.
- temple_sanctum: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, ruined temple sanctum, columns, ritual floor pattern without text, no grid.
- tavern_ground_floor: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, tavern common room, bar, tables, hearth, no grid.
- inn_guest_rooms: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, inn hallway and small guest rooms, no grid.
- village_street_market: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, village street with stalls and carts, no grid.
- blacksmith_workshop: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, forge, anvil, racks, worktables, no grid.
- forest_clearing: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, forest clearing with trees, logs, rocks, no grid.
- forest_road_ambush: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, winding road through dense woods, ambush cover, no grid.
- cave_entrance: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, rocky cave mouth and outside approach, no grid.
- cavern_lake: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, underground lake, ledges, stalagmites, no grid.
- mushroom_cavern: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, large fungi, damp stone, no grid.
- sewer_crossing: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, sewer channels, bridges, walkways, no grid.
- bridge_over_chasm: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, narrow bridge crossing dark chasm, no grid.
- river_ford: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, shallow river crossing and rocks, no grid.
- swamp_boardwalk: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, swamp water, wooden walkways, reeds, no grid.
- desert_ruins: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, sandy ruins, fallen columns, no grid.
- snowy_pass: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, icy mountain pass, boulders, snow drifts, no grid.
- ship_deck: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, wooden sailing ship deck, mast, cargo, no grid.
- wizard_laboratory: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, arcane lab, tables, books, apparatus, no readable text, no grid.
- throne_room: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, castle throne room, pillars, carpets, no grid.
- graveyard_night: BATTLE_MAP, 2048x1536 opaque PNG, 32x24 invisible 64 px cells, graveyard with blank stones, crypt entrance, no text, no grid.

CITY AND WORLD MAPS

- regional_overland_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, parchment regional map with west coast, eastern mountains, central river, forests, roads, villages indicated by unlabeled icons.
- kingdom_overland_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, larger kingdom map with coast, mountain range, plains, border roads, unlabeled settlements.
- frontier_valley_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, valley map with river, keep, forest, hills, cave entrances, no labels.
- island_campaign_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, island coastline, coves, inland jungle, ruins, roads, no labels.
- walled_city_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, top-down city cartography with walls, gates, river, districts, streets, no labels.
- port_city_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, harbor, docks, warehouses, old town, sea wall, no labels.
- village_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, small village map with cottages, inn, temple, farms, road, stream, no labels.
- dungeon_level_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, parchment-style dungeon overview map with rooms and corridors, no grid and no labels.
- cave_network_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, cave network overview with chambers, underground stream, no labels.
- planar_crossroads_map: CITY_OR_WORLD_MAP, 2048x1536 opaque PNG, stylized fantasy crossroads map with portals, standing stones, and roads, no labels and no readable symbols.

MAP PIECES (HEX-TILEABLE, REUSABLE)

Modular parts instead of monolithic maps: the master assembles a scene by placing and repeating these pieces on the pointy-top hex grid. Footprints are counted in hexes; edges are made to abut neighbors seamlessly.

- dungeon_floor_tile: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, seamless flagstone dungeon floor patch, tileable edges.
- stone_wall_straight: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, straight dressed-stone dungeon wall run along a hex row.
- stone_wall_corner: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, right-angle dungeon wall corner.
- stone_wall_t_junction: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, T-shaped dungeon wall junction.
- dungeon_corridor_straight: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, walled stone corridor section, tileable end to end.
- dungeon_corridor_bend: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, walled corridor bend.
- dungeon_doorway: MAP_PIECE, 512x512 transparent PNG, footprint 1x1 hexes, doorway opening in a stone wall with timber frame.
- dungeon_stairs: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, flight of stone stairs.
- dungeon_pit: MAP_PIECE, 512x512 transparent PNG, footprint 1x1 hexes, open floor pit with dark interior.
- dungeon_rubble_floor: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, collapsed rubble-strewn floor patch.
- cave_floor_tile: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, rough natural cavern floor patch, tileable.
- cave_wall_edge: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, natural cavern wall boundary.
- stalagmite_cluster_piece: MAP_PIECE, 512x512 transparent PNG, footprint 1x1 hexes, cluster of cave stalagmites.
- deep_water_tile: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, deep water patch, tileable.
- shallow_water_tile: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, shallow water or ford patch, tileable.
- water_shore_edge: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, land-to-water shoreline boundary.
- river_segment: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, flowing river section, tileable end to end.
- wooden_bridge_segment: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, wooden bridge span for water or chasm.
- grass_field_tile: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, open grass patch, tileable.
- dense_woods_patch: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, dense forest canopy cluster, top-down.
- dirt_road_straight: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, dirt road or trail section, tileable.
- rocky_ground_patch: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, broken rocky terrain patch.
- swamp_muck_tile: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, boggy muck and reeds, difficult terrain.
- lava_flow_segment: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, molten lava channel with muted glow, tileable.
- cobblestone_street: MAP_PIECE, 512x512 transparent PNG, footprint 2x2 hexes, paved town street patch, tileable.
- building_wall_segment: MAP_PIECE, 512x512 transparent PNG, footprint 2x1 hexes, timber-and-stone building wall run.

QUALITY CHECK

Before considering the set complete, verify that every transparent token has alpha transparency, no text, no frame, no grid, no base ring, and a circle-safe silhouette. Verify that every map is opaque, full bleed, top-down, label-free, and has no drawn grid. Verify that every MAP_PIECE is transparent, top-down, free of drawn grid lines, and tiles seamlessly on the pointy-top hex grid with edges that abut neighboring pieces rather than a circle-safe silhouette. Verify that all files match the requested canvas sizes exactly.
