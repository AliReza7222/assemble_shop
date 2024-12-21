from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth.models import Group, Permission
from faker import Faker

from assemble_shop.orders.models import Discount, Product, Review
from assemble_shop.orders.tests.factories import (
    DiscountFactory,
    ProductFactory,
    ReviewFactory,
)
from assemble_shop.users.groups import *
from assemble_shop.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from assemble_shop.users.models import User as UserType


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> UserType:
    return UserFactory()


@pytest.fixture
def faker() -> Faker:
    return Faker()


@pytest.fixture
def create_product(db) -> Callable:
    def _create(**kwargs) -> Product:
        return ProductFactory(**kwargs)

    return _create


@pytest.fixture
def create_review(db) -> Callable:
    def _create_review(**kwargs) -> Review:
        return ReviewFactory(**kwargs)

    return _create_review


@pytest.fixture
def create_discount(db) -> Callable:
    def _create_discount(**kwargs) -> Discount:
        return DiscountFactory(**kwargs)

    return _create_discount


@pytest.fixture
def create_user_with_permissions(db, user) -> Callable:
    def _create_user_with_permissions(group_name: str) -> UserType:
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = Permission.objects.filter(
            codename__in=PERMISIONS.get(group_name, [])
        )
        group.permissions.set(permissions)
        user.groups.add(group)
        user.is_staff = True
        user.save()
        return user

    return _create_user_with_permissions


@pytest.fixture
def user_admin(db, create_user_with_permissions):
    return create_user_with_permissions(ADMIN)


@pytest.fixture
def user_storemanager(db, create_user_with_permissions):
    return create_user_with_permissions(STOREMANAGER)


@pytest.fixture
def user_customer(db, create_user_with_permissions):
    return create_user_with_permissions(CUSTOMER)
