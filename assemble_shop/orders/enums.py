from assemble_shop.base.enums import BaseEnum


class OrderStatusEnum(BaseEnum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELED = "Canceled"
