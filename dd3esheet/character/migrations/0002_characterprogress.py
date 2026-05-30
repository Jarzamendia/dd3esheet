from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('character', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharacterProgress',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='character.character')),
                ('ExperiencePoints', models.IntegerField(blank=True, default=0, null=True)),
                ('CampaignName', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
    ]
