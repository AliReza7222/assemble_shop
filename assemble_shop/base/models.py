from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class BaseModel(models.Model):
    created_by = models.ForeignKey(
        User,
        verbose_name=_("Created By"),
        related_name="%(class)s_created_by",
        on_delete=models.DO_NOTHING,
    )
    updated_by = models.ForeignKey(
        User,
        verbose_name=_("Updated By"),
        related_name="%(class)s_updated_by",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = timezone.now()

        self.updated_at = timezone.now()

        super().save(*args, **kwargs)

    class Meta:
        abstract = True
