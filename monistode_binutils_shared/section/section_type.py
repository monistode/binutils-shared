import enum


class SectionType(enum.Enum):
    """The type of section."""

    TEXT = 0
    DATA = 1
    BSS = 2
    SYMBOL_TABLE = 3
    RELOCATION_TABLE = 4
