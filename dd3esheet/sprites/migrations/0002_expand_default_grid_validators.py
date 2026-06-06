from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('sprites', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spriteasset',
            name='DefaultGridHeight',
            field=models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(64)]),
        ),
        migrations.AlterField(
            model_name='spriteasset',
            name='DefaultGridWidth',
            field=models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(64)]),
        ),
    ]
