"""A location in the object file."""

from dataclasses import dataclass


@dataclass
class Location:
    """A location in the object file."""

    section: str
    offset: int

    def apply_offset(self, offset: int) -> "Location":
        """Apply an offset to the location."""
        return Location(self.section, self.offset + offset)
