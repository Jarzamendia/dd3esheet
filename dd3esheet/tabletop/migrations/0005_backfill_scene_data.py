from django.db import migrations


def backfill(apps, schema_editor):
    Token = apps.get_model('tabletop', 'Token')
    TerrainCell = apps.get_model('tabletop', 'TerrainCell')
    kind_to_faction = {'player': 'party', 'enemy': 'enemy', 'npc': 'neutral', 'object': 'neutral'}

    for token in Token.objects.all():
        token.Faction = kind_to_faction.get(token.Kind, 'enemy')
        token.save(update_fields=['Faction'])

    # terreno sem chave -> 'stone'
    TerrainCell.objects.filter(Terrain='').update(Terrain='stone')

    # FogRegion (retângulos, px) não converte fielmente para hexes sem o GridSize;
    # política: não migrar geometria. FogCell começa vazio; o mestre re-pinta a
    # névoa no novo editor (ver docs/known-issues.md).


class Migration(migrations.Migration):
    dependencies = [
        ('tabletop', '0004_terraincell_terrain_token_conditions_token_faction_and_more'),
    ]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
