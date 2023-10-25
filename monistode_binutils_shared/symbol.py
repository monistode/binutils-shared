"""A class representing a single symbol in the object file."""
from dataclasses import dataclass

from .location import Location


@dataclass
class Symbol:
    """A symbol as declared in a section."""

    location: Location
    name: str
