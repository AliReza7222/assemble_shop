# Generated by Django 5.0.9 on 2024-12-03 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_remove_order_products_orderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(related_name='orders', through='orders.OrderItem', to='orders.product', verbose_name='Products'),
        ),
    ]
