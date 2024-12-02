from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .groups import CUSTOMER
from .managers import UserManager


class User(AbstractUser):
    # First and last name do not cover name patterns around the globe
    name = models.CharField(
        verbose_name=_("Name of User"), blank=True, max_length=255
    )
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = models.EmailField(verbose_name=_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})

    def is_customer(self):
        return self.groups.filter(name__in=[CUSTOMER]).exists()

    class Meta:
        db_table = "users"
