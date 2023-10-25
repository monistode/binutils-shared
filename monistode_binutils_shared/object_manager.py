"""A manager for object files"""
from dataclasses import dataclass
import enum
import struct

from monistode_binutils_shared.section.text import Text

from .section import Section


class SectionType(enum.Enum):
    """The type of section."""

    TEXT = 0
    DATA = 1


@dataclass
class Parameters:
    """Parameters for the object manager."""

    opcode_size: int
    text_byte: int
    data_byte: int
    text_address: int
    data_address: int

    @classmethod
    def from_bytes(cls, file: bytes) -> "Parameters":
        """Create parameters from a file.

        Args:
            file (bytes): The file to read from.

        Returns:
            Parameters: The parameters.
        """
        return cls(*struct.unpack("<IIIII", file[:20]))

    def to_bytes(self) -> bytes:
        """Convert the parameters to a file.

        Returns:
            bytes: The file.
        """
        return struct.pack(
            "<IIIII",
            self.opcode_size,
            self.text_byte,
            self.data_byte,
            self.text_address,
            self.data_address,
        )

    def size(self) -> int:
        """Get the size of the parameters in bytes.

        Returns:
            int: The size of the parameters in bytes.
        """
        return struct.calcsize("<IIIII")


@dataclass
class SectionTableEntry:
    """An entry in the section table."""

    section_type: int
    section_size: int

    @classmethod
    def from_bytes(cls, file: bytes) -> "SectionTableEntry":
        """Create a section table entry from a file.

        Args:
            file (bytes): The file to read from.

        Returns:
            SectionTableEntry: The section table entry.
        """
        return cls(*struct.unpack("<II", file[:12]))

    def to_bytes(self) -> bytes:
        """Convert the section table entry to a file.

        Returns:
            bytes: The file.
        """
        return struct.pack("<II", self.section_type, self.section_size)

    @staticmethod
    def size() -> int:
        """Get the size of the section table entry in bytes.

        Returns:
            int: The size of the section table entry in bytes.
        """
        return struct.calcsize("<II")


@dataclass
class ObjectHeader:
    """The header of an object file."""

    parameters: Parameters
    section_table_size: int

    @classmethod
    def from_bytes(cls, file: bytes) -> "ObjectHeader":
        """Create an object header from a file.

        Args:
            file (bytes): The file to read from.

        Returns:
            ObjectHeader: The object header.
        """
        return cls(
            Parameters.from_bytes(file[:16]),
            *struct.unpack("<I", file[16:24]),
        )

    def to_bytes(self) -> bytes:
        """Convert the object header to a file.

        Returns:
            bytes: The file.
        """
        return self.parameters.to_bytes() + struct.pack("<I", self.section_table_size)

    def size(self) -> int:
        """Get the size of the object header in bytes.

        Returns:
            int: The size of the object header in bytes.
        """
        return self.parameters.size() + struct.calcsize("<I")


class ObjectManager:
    """A manager for object files"""

    def __init__(self, parameters: Parameters, data: bytes = b"") -> None:
        """Initialize the object manager."""
        self._data = bytearray(data)
        self._parameters = parameters
        self._sections: list[Section] = []

    @classmethod
    def from_bytes(cls, source: bytes) -> "ObjectManager":
        """Create an object manager from bytes.

        Args:
            source (bytes): The bytes to read from.

        Returns:
            ObjectManager: The object manager.
        """
        header = ObjectHeader.from_bytes(source)
        manager = cls(header.parameters, source)
        manager.load()
        return manager

    def to_bytes(self) -> bytes:
        """Convert the object manager to bytes.

        Returns:
            bytes: The bytes.
        """
        sections_data: list[bytes] = []
        sections_table: list[SectionTableEntry] = []
        for section in self._sections:
            sections_data.append(section.data)
            sections_table.append(
                SectionTableEntry(
                    SectionType[section.name.upper()].value,
                    len(section),
                ),
            )
        return (
            ObjectHeader(
                self._parameters,
                len(self._sections),
            ).to_bytes()
            + b"".join(entry.to_bytes() for entry in sections_table)
            + b"".join(sections_data)
        )

    def load(self) -> None:
        """Load the object file."""
        self._sections = []
        header = ObjectHeader.from_bytes(self._data)
        self._parameters = header.parameters
        table_offset = header.size()
        section_offset = (
            header.size() + SectionTableEntry.size() * header.section_table_size
        )
        for _ in range(header.section_table_size):
            section_entry = SectionTableEntry.from_bytes(self._data[table_offset:])
            table_offset += section_entry.size()
            section = self._section_from_bytes(
                section_entry.section_type,
                self._data[section_offset:],
                section_entry.section_size,
            )
            self._sections.append(
                section,
            )
            section_offset += len(section)

    def _section_from_bytes(self, section_type: int, data: bytes, size: int) -> Section:
        if section_type == SectionType.TEXT.value:
            text_section = Text(self._parameters.text_byte)
            text_section.from_bytes(data, size)
            return text_section
        raise ValueError(f"Unknown section type: {section_type}")

    def string_at(self, address: int) -> str:
        """Get the null-terminated string at the address.

        Args:
            address (int): The address of the string.

        Returns:
            str: The string.
        """
        return self._data[address : self._data.find(b"\x00", address)].decode("utf-8")

    def append_section(self, section: Section) -> None:
        """Append a section to the object file.

        Args:
            section (Section): The section to append.
        """
        self._sections.append(section)
