from enum import Enum


class BaseEnum(Enum):
    @classmethod
    def choices(cls):
        return [(member.name, member.value) for member in cls]
