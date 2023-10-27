"""A section representing the relocation table."""
import struct
from typing import Iterable

from ..location import Location
from ..relocation import RelocationTargetSymbol, SymbolRelocation
from ..segment.common import Segment
from ..symbol import Symbol
from .section_type import SectionType


class RelocationTable:
    """A section representing the relocation table."""

    name = "relocation_table"

    def __init__(self) -> None:
        """Initialize the symbol table."""
        self._relocations: list[SymbolRelocation] = []
        self.names: dict[bytes, int] = {}
        self._format = "<IIIIIII"

    def from_bytes(self, data: bytes, symbol_count: int) -> None:
        """Load the symbol table from bytes.

        Args:
            data (bytes): The bytes to read from.
            symbol_count (int): The number of symbols in the symbol table.
        """
        for i in range(symbol_count):
            offset = i * struct.calcsize(self._format)
            relocation_data = data[offset : offset + struct.calcsize(self._format)]
            (
                location_section_id,
                location_offset,
                name_addr,
                symbol_section_id,
                symbol_size,
                symbol_offset,
                relative,
            ) = struct.unpack(self._format, relocation_data)
            relocation_name = self.string_at(
                data,
                name_addr + symbol_count * struct.calcsize(self._format),
            )
            self._relocations.append(
                SymbolRelocation(
                    Location(
                        SectionType(location_section_id).name.lower(),
                        location_offset,
                    ),
                    RelocationTargetSymbol(
                        relocation_name,
                        SectionType(symbol_section_id).name.lower(),
                    ),
                    symbol_size,
                    symbol_offset,
                    relative,
                )
            )
            self.names[relocation_name.encode("utf-8")] = name_addr

    def __len__(self) -> int:
        """The virtual size of the relocation table."""
        return len(self._relocations)

    @property
    def physical_size(self) -> int:
        """The size of the section as it appears on disk."""
        return len(self.data)

    def append_name(self, name: str) -> None:
        """Append a name to the relocation table.

        Args:
            name (str): The name to append.
        """
        encoded_name = name.encode("utf-8")
        if encoded_name not in self.names:
            self.names[encoded_name] = sum(len(name) + 1 for name in self.names.keys())

    @property
    def data(self) -> bytes:
        """The data contained in the relocation table."""
        output = b""
        for relocation in self._relocations:
            output += self.relocation_data(relocation)
        for name in sorted(self.names.keys(), key=lambda name: self.names[name]):
            output += name + b"\x00"
        return output

    def relocation_data(self, relocation: SymbolRelocation) -> bytes:
        """The data contained in a relocation.

        Args:
            relocation (SymbolRelocation): The relocation.

        Returns:
            bytes: The data.
        """
        return struct.pack(
            self._format,
            self.section_name_to_id(relocation.location.section),
            relocation.location.offset,
            self.names[relocation.symbol.name.encode("utf-8")],
            self.section_name_to_id(relocation.symbol.section_name),
            relocation.size,
            relocation.offset,
            relocation.relative,
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

    def append(self, relocation: SymbolRelocation) -> None:
        """Append a relocation to the relocation table.

        Args:
            relocation (SymbolRelocation): The relocation to append.
        """
        self._relocations.append(relocation)
        self.append_name(relocation.symbol.name)

    def string_at(self, data: bytes, address: int) -> str:
        """Get the null-terminated string at the address.

        Args:
            address (int): The address of the string.
            data (bytes): The data to read from.

        Returns:
            str: The string.
        """
        return data[address : data.find(b"\x00", address)].decode("utf-8")

    def __iter__(self) -> Iterable[SymbolRelocation]:
        """Iterate over the relocations in the relocation table.

        Returns:
            iter[Symbol]: An iterator over the relocations.
        """
        for relocation in self._relocations:
            yield relocation

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

    def merge(self, other: "RelocationTable") -> None:
        """Merge another relocation table into this one.

        Args:
            other (RelocationTable): The other relocation table.
        """
        raise NotImplementedError

    def segments(self) -> tuple[Segment, ...]:
        """Get the segments of the symbol table.

        Returns:
            list[bytes]: The segments.
        """
        return ()
