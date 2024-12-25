from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth.models import Group, Permission
from django.forms.models import inlineformset_factory
from django.utils import timezone
from faker import Faker

from assemble_shop.orders.enums import OrderStatusEnum
from assemble_shop.orders.formsets import OrderItemFormset
from assemble_shop.orders.models import Discount, OrderItem, Product, Review
from assemble_shop.orders.tests.factories import *
from assemble_shop.users.groups import *
from assemble_shop.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from assemble_shop.users.models import User as UserType


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def create_user(db) -> Callable:
    def _create_user(**kwargs) -> UserType:
        return UserFactory(**kwargs)

    return _create_user


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
def product_with_discount(db, create_discount) -> Product:
    product = ProductFactory(name="CheapProduct")
    create_discount(
        product=product,
        discount_percentage=Decimal("99.99"),
        start_date=timezone.now(),
        end_date=timezone.now() + timezone.timedelta(days=7),  # type: ignore
        is_active=True,
    )
    return product


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
def create_user_with_permissions(db, create_user) -> Callable:
    def _create_user_with_permissions(group_name: str) -> UserType:
        user = create_user(is_staff=True)
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = Permission.objects.filter(
            codename__in=PERMISIONS.get(group_name, [])
        )
        group.permissions.set(permissions)
        user.groups.add(group)
        return user

    return _create_user_with_permissions


@pytest.fixture
def client_authenticated(client, create_user):
    user = create_user(is_staff=True)
    client.force_login(user)
    return client


@pytest.fixture
def user_admin(db, create_user_with_permissions):
    return create_user_with_permissions(ADMIN)


@pytest.fixture
def user_storemanager(db, create_user_with_permissions):
    return create_user_with_permissions(STOREMANAGER)


@pytest.fixture
def user_customer(db, create_user_with_permissions):
    return create_user_with_permissions(CUSTOMER)


@pytest.fixture
def create_order(db):
    def _create_order(products: list = [], **kwargs):
        return OrderWithMultipleOrderItem(products=products, **kwargs)

    return _create_order


@pytest.fixture
def orderitem_inline_formset(db, create_order):
    def _orderitem_inline_formset(data: dict = {}):
        order = create_order()
        inline_formset = inlineformset_factory(  # type: ignore
            Order, OrderItem, formset=OrderItemFormset, fields="__all__"
        )
        return inline_formset(data=data, instance=order)

    return _orderitem_inline_formset


@pytest.fixture
def data_orderitem_inline(db, create_product, create_order):
    def _data_orderitem_inline(
        status: str = OrderStatusEnum.PENDING.name, has_items: bool = False
    ):
        product = create_product(name="ProductTest", inventory=10)
        items = [product] if has_items else []
        order = create_order(products=items, status=status)
        post_data = {
            "status": status,
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-0-product": product.pk,
            "items-0-quantity": 1,
            "items-0-order": order.pk,
        }
        return product, order, post_data

    return _data_orderitem_inline
