# Generated by Django 4.2.11 on 2024-04-12 00:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_characterweapon'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharacterArcaneSpellFailCheck',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='base.character')),
                ('Value', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterAttackModifiers',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='base.character')),
                ('BBA', models.IntegerField(blank=True, default=0, null=True)),
                ('SpellResistence', models.IntegerField(blank=True, default=0, null=True)),
                ('TotalGrappler', models.IntegerField(blank=True, default=0, null=True)),
                ('GrapplerBBA', models.IntegerField(blank=True, default=0, null=True)),
                ('GrapplerStrModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('GrapplerSizeModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('GrapplerMiscModifier', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterMagicConditionalModifiers',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='base.character')),
                ('Value', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterMoney',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='base.character')),
                ('CP', models.IntegerField(blank=True, default=0, null=True)),
                ('SP', models.IntegerField(blank=True, default=0, null=True)),
                ('GP', models.IntegerField(blank=True, default=0, null=True)),
                ('PP', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterOtherItemObs',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='base.character')),
                ('LightLoad', models.IntegerField(blank=True, default=0, null=True)),
                ('MediumLoad', models.IntegerField(blank=True, default=0, null=True)),
                ('HeavyLoad', models.IntegerField(blank=True, default=0, null=True)),
                ('LiftOverHEad', models.IntegerField(blank=True, default=0, null=True)),
                ('LiftOffGround', models.IntegerField(blank=True, default=0, null=True)),
                ('PushOrDrag', models.IntegerField(blank=True, default=0, null=True)),
                ('TotalWCarried', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterSavingThrows',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='base.character')),
                ('TotalFortitude', models.IntegerField(blank=True, default=0, null=True)),
                ('FortitudeBaseSave', models.IntegerField(blank=True, default=0, null=True)),
                ('FortitudeAbilityModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('FortitudeMagicModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('FortitudeMiscModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('FortitudeTemporaryModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('FortitudeConditionalModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('TotalReflex', models.IntegerField(blank=True, default=0, null=True)),
                ('ReflexBaseSave', models.IntegerField(blank=True, default=0, null=True)),
                ('ReflexAbilityModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('ReflexMagicModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('ReflexMiscModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('ReflexTemporaryModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('ReflexConditionalModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('TotalWill', models.IntegerField(blank=True, default=0, null=True)),
                ('WillBaseSave', models.IntegerField(blank=True, default=0, null=True)),
                ('WillAbilityModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('WillMagicModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('WillMiscModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('WillTemporaryModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('WillConditionalModifier', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('SkillIsActive', models.BinaryField(blank=True, default=0, null=True)),
                ('SkillName', models.CharField(blank=True, max_length=200, null=True)),
                ('SkillAbility', models.IntegerField(blank=True, default=0, null=True)),
                ('SkillModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('AbilityModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('Ranks', models.IntegerField(blank=True, default=0, null=True)),
                ('MiscModifier', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterSkillGraduation',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='base.character')),
                ('MaxGraduation', models.IntegerField(blank=True, default=0, null=True)),
                ('OtherClassMaxGraduation', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterSpellSave',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='base.character')),
                ('Value', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterStatus',
            fields=[
                ('Character', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='base.character')),
                ('TotalHitPoints', models.IntegerField(blank=True, default=0, null=True)),
                ('NonLethalDamager', models.IntegerField(blank=True, default=0, null=True)),
                ('Speed', models.IntegerField(blank=True, default=0, null=True)),
                ('ACTotal', models.IntegerField(blank=True, default=0, null=True)),
                ('ACArmorBonus', models.IntegerField(blank=True, default=0, null=True)),
                ('ACShieldBonus', models.IntegerField(blank=True, default=0, null=True)),
                ('ACDexModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('ACSizeModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('ACNaturalArmor', models.IntegerField(blank=True, default=0, null=True)),
                ('ACDeflectionModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('ACMiscModifier', models.IntegerField(blank=True, default=0, null=True)),
                ('DamageReduction', models.IntegerField(blank=True, default=0, null=True)),
                ('ACTouch', models.IntegerField(blank=True, default=0, null=True)),
                ('ACFlatFooterd', models.IntegerField(blank=True, default=0, null=True)),
                ('Initiative', models.IntegerField(blank=True, default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CharacterSpell',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('Page', models.CharField(blank=True, max_length=200, null=True)),
                ('Level', models.IntegerField(blank=True, default=0, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
        migrations.CreateModel(
            name='CharacterShield',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('ACBonus', models.CharField(blank=True, max_length=200, null=True)),
                ('Weigth', models.CharField(blank=True, max_length=200, null=True)),
                ('CheckPenalty', models.CharField(blank=True, max_length=200, null=True)),
                ('SpellFailure', models.CharField(blank=True, max_length=200, null=True)),
                ('SpecialProperties', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
        migrations.CreateModel(
            name='CharacterProtectionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('ACBonus', models.CharField(blank=True, max_length=200, null=True)),
                ('Weigth', models.CharField(blank=True, max_length=200, null=True)),
                ('SpecialProperties', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
        migrations.CreateModel(
            name='CharacterOtherItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('Page', models.CharField(blank=True, max_length=200, null=True)),
                ('Weigth', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
        migrations.CreateModel(
            name='CharacterMagicDayUse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Level', models.IntegerField(blank=True, default=0, null=True)),
                ('SpellsKnown', models.IntegerField(blank=True, default=0, null=True)),
                ('SpellSaveDC', models.IntegerField(blank=True, default=0, null=True)),
                ('SpellsPerDay', models.IntegerField(blank=True, default=0, null=True)),
                ('BonusSpells', models.IntegerField(blank=True, default=0, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
        migrations.CreateModel(
            name='CharacterLanguages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Value', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
        migrations.CreateModel(
            name='CharacterFeat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('Page', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
        migrations.CreateModel(
            name='CharacterArmor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('Type', models.CharField(blank=True, max_length=200, null=True)),
                ('ACBonus', models.CharField(blank=True, max_length=200, null=True)),
                ('MaxDex', models.CharField(blank=True, max_length=200, null=True)),
                ('CheckPenalty', models.CharField(blank=True, max_length=200, null=True)),
                ('SpellFailure', models.CharField(blank=True, max_length=200, null=True)),
                ('Speed', models.CharField(blank=True, max_length=200, null=True)),
                ('Weigth', models.CharField(blank=True, max_length=200, null=True)),
                ('SpecialProperties', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
        migrations.CreateModel(
            name='Ability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(blank=True, max_length=200, null=True)),
                ('Page', models.CharField(blank=True, max_length=200, null=True)),
                ('Character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.character')),
            ],
        ),
    ]
