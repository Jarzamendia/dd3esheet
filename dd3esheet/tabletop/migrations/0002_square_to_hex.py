from django.db import migrations, models


def square_to_hex(apps, schema_editor):
    Map = apps.get_model('tabletop', 'Map')
    Map.objects.filter(GridMode='square').update(GridMode='hex')


def hex_to_square(apps, schema_editor):
    Map = apps.get_model('tabletop', 'Map')
    Map.objects.filter(GridMode='hex').update(GridMode='square')


class Migration(migrations.Migration):

    dependencies = [
        ('tabletop', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='map',
            name='GridMode',
            field=models.CharField(
                max_length=8,
                default='hex',
                choices=[('hex', 'Hexagonal'), ('free', 'Livre')],
            ),
        ),
        migrations.RunPython(square_to_hex, hex_to_square),
    ]
