from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from assemble_shop.users.groups import PERMISIONS


class Command(BaseCommand):
    help = "Creating groups for the store."

    @transaction.atomic
    def handle(self, *args, **options):
        for group_name, group_permission in PERMISIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)

            group.permissions.clear()

            permissions = Permission.objects.filter(
                codename__in=group_permission
            )
            group.permissions.set(permissions)

            message = (
                self.style.SUCCESS(
                    f"Created '{group_name}' group successfully and assigned the permissions."
                )
                if created
                else self.style.WARNING(f"{group_name} group already exists.")
            )
            self.stdout.write(message)
