"""A relocation entry for the object file."""
from dataclasses import dataclass

from .location import Location


@dataclass
class RelocationTargetSymbol:
    """A symbol as declared in a section."""

    name: str
    section_name: str


@dataclass
class SymbolRelocationParams:
    """Parameters for a symbol relocation.

    Adds to the bits at location with the address of target.
    (the offset here is the number of bits to add to the location,
    as the location is a byte address)
    """

    target: RelocationTargetSymbol
    offset: int
    relative: bool


@dataclass
class SymbolRelocation:
    """A relocation entry for the object file."""

    location: Location
    symbol: RelocationTargetSymbol
    offset: int
    relative: bool

    @classmethod
    def from_params(
        cls, location: Location, params: SymbolRelocationParams
    ) -> "SymbolRelocation":
        """Create a symbol relocation from parameters.

        Args:
            location (Location): The location of the relocation.
            params (SymbolRelocationParams): The parameters for the relocation.

        Returns:
            SymbolRelocation: The symbol relocation.
        """
        return cls(
            location,
            params.target,
            params.offset,
            params.relative,
        )
