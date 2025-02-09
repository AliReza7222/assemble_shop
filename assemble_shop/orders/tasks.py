from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .enums import OrderStatusEnum
from .models import Order


@shared_task
def cancel_old_pending_order():
    time_threshold = timezone.now() - timedelta(hours=5)  # 5 hours ago

    with transaction.atomic():
        count = Order.objects.filter(
            created_at__lte=time_threshold, status=OrderStatusEnum.PENDING.name
        ).update(
            status=OrderStatusEnum.CANCELED.name
        )  # orders 5 hours ago

    return f"{count} old pending orders were canceled."
