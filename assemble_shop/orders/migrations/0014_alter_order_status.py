# Generated by Django 5.0.9 on 2024-12-03 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0013_remove_orderitem_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('COMPLETED', 'Completed'), ('CANCELED', 'Canceled')], default='PENDING', max_length=50, verbose_name='Status'),
        ),
    ]