"""A class representing a single section in the object file."""
from typing import Protocol, Self

from ..relocation import SymbolRelocation
from ..segment import Segment
from ..symbol import Symbol


class Section(Protocol):
    """A class representing a single section in the object file."""

    name: str

    def __len__(self) -> int:
        """The size of the section in bytes.
        Will only be used for relocations when merging sections;
        should represent the expected size of the section after
        loading into memory.
        """

    @property
    def physical_size(self) -> int:
        """The size of the section as it appears on disk."""

    @property
    def data(self) -> bytes:
        """The data contained in the section, in a format that
        can be written to a file.
        """

    @property
    def symbols(self) -> list[Symbol]:
        """A list of symbols in the section."""

    @property
    def relocations(self) -> list[SymbolRelocation]:
        """A list of relocations in the section."""

    def add_symbol(self, symbol: Symbol) -> None:
        """Add a symbol to the section."""

    def add_relocation(self, relocation: SymbolRelocation) -> None:
        """Add a relocation to the section."""

    def merge(self, other: Self) -> None:
        """Merge another section into this one."""

    def segments(self) -> tuple[Segment, ...]:
        """Convert the section into a list of segments."""
