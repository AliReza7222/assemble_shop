# Generated by Django 5.0.9 on 2024-12-01 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_alter_discount_discount_percentage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='rating',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True, verbose_name='Rating'),
        ),
    ]
