"""A section representing the symbol table."""
import struct
from typing import Iterable

from ..location import Location
from ..relocation import SymbolRelocation
from ..segment.common import Segment
from ..symbol import Symbol
from .section_type import SectionType


class SymbolTable:
    """A section representing the symbol table."""

    name = "symbol_table"

    def __init__(self) -> None:
        """Initialize the symbol table."""
        self._symbols: list[Symbol] = []
        self.names: dict[bytes, int] = {}
        self._format = "<III"

    def from_bytes(self, data: bytes, symbol_count: int) -> None:
        """Load the symbol table from bytes.

        Args:
            data (bytes): The bytes to read from.
            symbol_count (int): The number of symbols in the symbol table.
        """
        for i in range(symbol_count):
            offset = i * struct.calcsize(self._format)
            symbol_data = data[offset : offset + struct.calcsize(self._format)]
            (
                section_id,
                offset,
                name_addr,
            ) = struct.unpack(self._format, symbol_data)
            symbol_name = self.string_at(
                data,
                name_addr + symbol_count * struct.calcsize(self._format),
            )
            self._symbols.append(
                Symbol(
                    Location(SectionType(section_id).name.lower(), offset),
                    symbol_name,
                ),
            )
            self.names[symbol_name.encode("utf-8")] = name_addr

    def __len__(self) -> int:
        """The virtual size of the symbol table."""
        return len(self._symbols)

    @property
    def physical_size(self) -> int:
        """The size of the section as it appears on disk."""
        return len(self.data)

    def append_name(self, name: str) -> None:
        """Append a name to the symbol table.

        Args:
            name (str): The name to append.
        """
        encoded_name = name.encode("utf-8")
        if encoded_name not in self.names:
            self.names[encoded_name] = sum(len(name) + 1 for name in self.names.keys())

    @property
    def data(self) -> bytes:
        """The data contained in the symbol table."""
        output = b""
        for symbol in self._symbols:
            output += self.symbol_data(symbol)
        for name in sorted(self.names.keys(), key=lambda name: self.names[name]):
            output += name + b"\x00"
        return output

    def symbol_data(self, symbol: Symbol) -> bytes:
        """The data contained in a symbol.

        Args:
            symbol (Symbol): The symbol.

        Returns:
            bytes: The data.
        """
        return struct.pack(
            self._format,
            self.section_name_to_id(symbol.location.section),
            symbol.location.offset,
            self.names[symbol.name.encode("utf-8")],
        )

    def section_name_to_id(self, name: str) -> int:
        """Convert a section name to an id.

        Args:
            name (str): The name.

        Returns:
            int: The id.
        """
        return SectionType[name.upper()].value

    @property
    def symbols(self) -> list[Symbol]:
        """A list of symbols in the symbol table."""
        return []

    @property
    def relocations(self) -> list[SymbolRelocation]:
        """A list of relocations in the symbol table."""
        return []

    def append(self, symbol: Symbol) -> None:
        """Append a symbol to the symbol table.

        Args:
            symbol (Symbol): The symbol to append.
        """
        if symbol.name in self.names:
            raise ValueError(f"Symbol {symbol.name} already exists in symbol table.")
        self._symbols.append(symbol)
        self.append_name(symbol.name)

    def string_at(self, data: bytes, address: int) -> str:
        """Get the null-terminated string at the address.

        Args:
            address (int): The address of the string.
            data (bytes): The data to read from.

        Returns:
            str: The string.
        """
        return data[address : data.find(b"\x00", address)].decode("utf-8")

    def __iter__(self) -> Iterable[Symbol]:
        """Iterate over the symbols in the symbol table.

        Returns:
            iter[Symbol]: The iterator.
        """
        for symbol in self._symbols:
            yield symbol

    def add_symbol(self, symbol: Symbol) -> None:
        """Add a symbol to the symbol table.

        Args:
            symbol (Symbol): The symbol to add.
        """
        raise NotImplementedError

    def add_relocation(self, relocation: SymbolRelocation) -> None:
        """Add a relocation to the symbol table.

        Args:
            relocation (SymbolRelocation): The relocation to add.
        """
        raise NotImplementedError

    def merge(self, other: "SymbolTable") -> None:
        """Merge another symbol table into this one.

        Args:
            other (SymbolTable): The other symbol table.
        """
        raise NotImplementedError

    def segments(self) -> tuple[Segment, ...]:
        """Get the segments of the symbol table.

        Returns:
            list[bytes]: The segments.
        """
        return ()
