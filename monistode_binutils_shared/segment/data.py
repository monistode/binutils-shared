"""A wrapper around the data section that turns it into a segment."""
from __future__ import annotations
from typing import TYPE_CHECKING

from ..bytearray import ByteArray
from ..executable import Flags
from ..relocation import SymbolRelocation
from ..symbol import Symbol

if TYPE_CHECKING:
    from ..section.data import Data


class DataSegment:
    """A segment that wraps the data section."""

    def __init__(self, data_section: Data) -> None:
        """Initialize the segment."""
        self._data_section = data_section

    def data(self) -> ByteArray:
        """Return the data of the segment."""
        return self._data_section._data

    def symbols(self, offset: int) -> tuple[Symbol, ...]:
        """Return the symbols in the segment."""
        return tuple(
            Symbol(symbol.location.apply_offset(offset), symbol.name)
            for symbol in self._data_section.symbols
        )

    @property
    def byte_size(self) -> int:
        """Return the size of a single byte in the segment."""
        return self._data_section.byte

    @property
    def size(self) -> int:
        """Return the size of the segment in its own bytes."""
        return len(self._data_section)

    @property
    def relocations(self) -> list[SymbolRelocation]:
        """Return the relocations in the segment."""
        return self._data_section.relocations

    @property
    def flags(self) -> Flags:
        """Return the flags of the segment."""
        return Flags(
            executable=False,
            writable=True,
            readable=True,
        )
