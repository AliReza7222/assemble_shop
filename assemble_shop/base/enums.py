from enum import Enum

from assemble_shop.base.fields import BASE_FIELDS


class BaseEnum(Enum):
    @classmethod
    def choices(cls):
        return [(member.name, member.value) for member in cls]


class BaseFieldsEnum(BaseEnum):
    BASE = BASE_FIELDS


class BaseTitleEnum(BaseEnum):
    GENERAL = "General"
    INFO = "Information"
