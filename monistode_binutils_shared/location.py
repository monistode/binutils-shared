"""A location in the object file."""

from dataclasses import dataclass


@dataclass
class Location:
    """A location in the object file."""

    section: str
    offset: int
