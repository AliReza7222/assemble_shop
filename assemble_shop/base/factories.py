from factory import SubFactory
from factory.django import DjangoModelFactory

from assemble_shop.users.tests.factories import UserFactory


class BaseFactory(DjangoModelFactory):
    created_by = SubFactory(UserFactory, email="test@gmail.com")

    class Meta:
        abstract = True
