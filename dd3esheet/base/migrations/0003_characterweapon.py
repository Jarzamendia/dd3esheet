# Generated by Django 4.2.11 on 2024-04-10 00:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_remove_character_characterstats_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharacterWeapon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('Attack', models.CharField(blank=True, max_length=200, null=True)),
                ('AttackBonus', models.CharField(blank=True, max_length=200, null=True)),
                ('Damage', models.CharField(blank=True, max_length=200, null=True)),
                ('Critical', models.CharField(blank=True, max_length=200, null=True)),
                ('Range', models.CharField(blank=True, max_length=200, null=True)),
                ('Type', models.CharField(blank=True, max_length=200, null=True)),
                ('Notes', models.CharField(blank=True, max_length=200, null=True)),
                ('AmmunitionName', models.CharField(blank=True, max_length=200, null=True)),
                ('AmmunitionCount', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
    ]