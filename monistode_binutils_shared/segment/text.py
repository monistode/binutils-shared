"""A wrapper around the text section that turns it into a segment."""
from __future__ import annotations
from typing import TYPE_CHECKING

from ..bytearray import ByteArray
from ..executable import Flags
from ..relocation import SymbolRelocation
from ..symbol import Symbol

if TYPE_CHECKING:
    from ..section.text import Text


class TextSegment:
    """A segment that wraps the text section."""

    def __init__(self, text_section: Text) -> None:
        """Initialize the segment."""
        self._text_section = text_section

    def data(self) -> ByteArray:
        """Return the data of the segment."""
        return self._text_section._data

    def symbols(self, offset: int) -> tuple[Symbol, ...]:
        """Return the symbols in the segment."""
        return tuple(
            Symbol(symbol.location.apply_offset(offset), symbol.name)
            for symbol in self._text_section.symbols
        )

    @property
    def byte_size(self) -> int:
        """Return the size of a single byte in the segment."""
        return self._text_section.byte

    @property
    def size(self) -> int:
        """Return the size of the segment in its own bytes."""
        return len(self._text_section)

    @property
    def relocations(self) -> list[SymbolRelocation]:
        """Return the relocations in the segment."""
        return self._text_section.relocations

    @property
    def flags(self) -> Flags:
        """Return the flags of the segment."""
        return Flags(
            executable=True,
            writable=False,
            readable=True,
        )
