# Generated by Django 5.0.9 on 2025-01-09 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_discount_discount_active_idx_order_order_status_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images_product/'),
        ),
    ]
