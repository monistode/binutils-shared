"""A class representing a single section in the object file."""
from typing import Protocol

from ..relocation import SymbolRelocation
from ..symbol import Symbol


class Section(Protocol):
    """A class representing a single section in the object file."""

    name: str

    def __len__(self) -> int:
        """The size of the section in bytes."""

    @property
    def data(self) -> bytes:
        """The data contained in the section."""

    @property
    def symbols(self) -> list[Symbol]:
        """A list of symbols in the section."""

    @property
    def relocations(self) -> list[SymbolRelocation]:
        """A list of relocations in the section."""
