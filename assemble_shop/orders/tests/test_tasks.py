from freezegun import freeze_time

from assemble_shop.orders.enums import OrderStatusEnum
from assemble_shop.orders.tasks import cancel_old_pending_order


class TestOrderTasks:
    def test_cancel_old_pending_order(self, create_order):
        with freeze_time("2024-02-09 12:00:00"):
            old_order = create_order()

        with freeze_time("2024-02-09 17:00:00"):
            recent_order = create_order()

            result = cancel_old_pending_order.apply()
            result.get()

        recent_order.refresh_from_db()
        old_order.refresh_from_db()

        assert old_order.status == OrderStatusEnum.CANCELED.name
        assert recent_order.status == OrderStatusEnum.PENDING.name
