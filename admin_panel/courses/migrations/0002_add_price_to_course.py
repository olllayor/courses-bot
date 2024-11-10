
from django.db import migrations, models
import django.core.validators

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='price',
            field=models.DecimalField(
                max_digits=7,
                decimal_places=2,
                default=0.00,
                validators=[django.core.validators.MinValueValidator(0)],
                help_text="Course price in UZS"
            ),
        ),
    ]