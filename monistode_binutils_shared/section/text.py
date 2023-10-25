"""The text section of the object file."""
from typing import Iterator

from monistode_binutils_shared.location import Location

from ..bytearray import ByteArray
from ..relocation import SymbolRelocation, SymbolRelocationParams
from ..symbol import Symbol


class Text:
    """The text section of the object file."""

    name = "text"

    def __init__(self, byte: int) -> None:
        """Initialize the text section.

        Args:
            byte (int): The byte to start at.
            address_bits (int): The number of bits in an address.
        """
        self._byte = byte
        self._data = ByteArray(byte)
        self._symbols: list[Symbol] = []
        self._relocations: list[SymbolRelocation] = []

    @property
    def byte(self) -> int:
        """The byte to start at."""
        return self._byte

    def __len__(self) -> int:
        """The size of the section in bytes."""
        return len(self._data)

    @property
    def data(self) -> bytes:
        """The data contained in the section."""
        return bytes(self._data)

    @property
    def symbols(self) -> list[Symbol]:
        """A list of symbols in the section."""
        return self._symbols

    @property
    def relocations(self) -> list[SymbolRelocation]:
        """A list of relocations in the section."""
        return self._relocations

    def add_symbol(self, name: str, address: int | None = None) -> None:
        """Add a symbol to the section at the address or the current byte.

        Args:
            name (str): The name of the symbol.
            address (int | None): The address of the symbol. Defaults to None.
        """
        self._symbols.append(
            Symbol(Location(self.name, len(self) if address is None else address), name)
        )

    def add_relocation(
        self,
        params: SymbolRelocationParams,
    ) -> None:
        """Add a relocation to the section at the current byte.

        Args:
            params (SymbolRelocationParams): The parameters for the relocation.
        """
        self._relocations.append(
            SymbolRelocation.from_params(
                Location(self.name, len(self)),
                params,
            )
        )

    def add_byte(self, byte: int) -> None:
        """Add a byte to the section.

        Args:
            byte (int): The byte to add.
        """
        self._data.append(byte)

    def from_bytes(self, data: bytes, length: int) -> None:
        """Add bytes to the section.

        Args:
            data (bytes): The bytes to add.
            length (int): The number of bytes to add.
        """
        self._data.from_bytes(data, length)

    def __iter__(self) -> Iterator[int]:
        """Iterate over the bytes in the section."""
        return iter(self._data)
