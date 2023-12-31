from dataclasses import dataclass
import struct
from typing import Protocol

from ..bytearray import ByteArray
from ..relocation import SymbolRelocation
from ..symbol import Symbol


@dataclass
class Flags:
    """A class representing the flags of a segment."""

    executable: bool
    writable: bool
    readable: bool
    special: bool = False
    stripped: bool = False

    def __bytes__(self) -> bytes:
        """Return the flags as a byte."""
        return struct.pack(
            "B",
            (self.stripped << 4)
            | (self.special << 3)
            | (self.readable << 2)
            | (self.writable << 1)
            | self.executable,
        )

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> "Flags":
        """Return the flags from a byte."""
        return cls(
            executable=bool(bytes_[0] & 0b1),
            writable=bool(bytes_[0] & 0b10),
            readable=bool(bytes_[0] & 0b100),
            special=bool(bytes_[0] & 0b1000),
            stripped=bool(bytes_[0] & 0b10000),
        )

    def __len__(self) -> int:
        """Return the length of the flags, in bytes."""
        return 1


class Segment(Protocol):
    """A class representing a single segment in the executable."""

    def data(self) -> ByteArray | None:
        """The data contained in the segment, or None if the
        segment should be zero-initialized.
        """

    def symbols(self, offset: int) -> tuple[Symbol, ...]:
        """All symbols in the segment."""

    @property
    def byte_size(self) -> int:
        """The size of a single byte in the segment."""

    @property
    def size(self) -> int:
        """The size of the segment in its own bytes."""

    @property
    def flags(self) -> Flags:
        """The flags of the segment."""

    @property
    def relocations(self) -> list[SymbolRelocation]:
        """A list of relocations in the segment."""
