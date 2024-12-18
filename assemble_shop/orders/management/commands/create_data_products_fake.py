import decimal
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from assemble_shop.orders.models import Product
from assemble_shop.users.models import User


class Command(BaseCommand):
    help = "This command is for creating many obj of 'Product' model."

    def get_user(self):
        email = input("Enter your email : ")
        user = User.objects.filter(email=email).first()
        if user:
            return user

        self.stdout.write(
            self.style.ERROR("Doesn't exists any user with this email !")
        )
        return

    def get_product_names(self, fake):
        return {fake.company() for _ in range(500)}

    @transaction.atomic
    def handle(self, *args, **kwargs):
        fake = Faker()
        created_by = self.get_user()
        product_names = self.get_product_names(fake)
        existing_names = set(
            Product.objects.filter(name__in=product_names).values_list(
                "name", flat=True
            )
        )
        bulk_list = []

        if not created_by:
            return

        for product_name in product_names:
            if product_name in existing_names:
                self.stdout.write(
                    self.style.ERROR(
                        f"Product with name '{product_name}' already exists !"
                    )
                )
                continue

            obj = Product(
                created_by=created_by,
                name=product_name,
                price=decimal.Decimal(random.randrange(10000)) / 100,
                inventory=random.randrange(10, 100),
            )
            bulk_list.append(obj)
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created product '{obj}''")
            )

        Product.objects.bulk_create(bulk_list)
