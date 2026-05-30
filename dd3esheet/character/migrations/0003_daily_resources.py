from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('character', '0002_characterprogress'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharacterDailyNotes',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='character.character')),
                ('Preparation', models.TextField(blank=True, null=True)),
                ('Spent', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterDailyResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('Source', models.CharField(blank=True, max_length=200, null=True)),
                ('Maximum', models.IntegerField(blank=True, default=0, null=True)),
                ('Used', models.IntegerField(blank=True, default=0, null=True)),
                ('Remaining', models.IntegerField(blank=True, default=0, null=True)),
                ('Refresh', models.CharField(blank=True, max_length=200, null=True)),
                ('Checks', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='character.character')),
            ],
        ),
        migrations.CreateModel(
            name='CharacterActiveEffect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('Source', models.CharField(blank=True, max_length=200, null=True)),
                ('Modifier', models.CharField(blank=True, max_length=200, null=True)),
                ('RoundsRemaining', models.IntegerField(blank=True, default=0, null=True)),
                ('Notes', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='character.character')),
            ],
        ),
    ]
