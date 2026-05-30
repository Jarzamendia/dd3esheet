from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('character', '0003_daily_resources'),
    ]

    operations = [
        migrations.AddField(
            model_name='characterskill',
            name='SkillSpecialization',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='characterskill',
            name='SkillAbility',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
