"""A manager for object files"""
from dataclasses import dataclass
import struct
from typing import Iterator

from monistode_binutils_shared.section.relocation_table import RelocationTable
from monistode_binutils_shared.section.symbol_table import SymbolTable
from monistode_binutils_shared.section.text import Text

from .section import Section, SectionType


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

    def summary(self) -> str:
        """Generate a human-readable summary of the object header.

        Returns:
            str: The summary.
        """
        return (
            f"Parameters:\n"
            f"  Opcode size: {self.opcode_size}\n"
            f"  Text byte: {self.text_byte}\n"
            f"  Data byte: {self.data_byte}\n"
            f"  Text address: {self.text_address}\n"
            f"  Data address: {self.data_address}\n"
        )


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
        return cls(*struct.unpack("<II", file[: cls.size()]))

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
        parameters = Parameters.from_bytes(file)
        return cls(
            parameters,
            *struct.unpack("<I", file[parameters.size() : parameters.size() + 4]),
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
        symbol_table = SymbolTable()
        relocation_table = RelocationTable()
        for section in self._sections:
            if isinstance(section, SymbolTable):
                continue
            sections_data.append(section.data)
            sections_table.append(
                SectionTableEntry(
                    SectionType[section.name.upper()].value,
                    len(section),
                ),
            )
            for symbol in section.symbols:
                symbol_table.append(symbol)
            for relocation in section.relocations:
                relocation_table.append(relocation)
        sections_data.append(symbol_table.data)
        sections_table.append(
            SectionTableEntry(
                SectionType.SYMBOL_TABLE.value,
                len(symbol_table),
            ),
        )
        sections_data.append(relocation_table.data)
        sections_table.append(
            SectionTableEntry(
                SectionType.RELOCATION_TABLE.value,
                len(relocation_table),
            ),
        )
        return (
            ObjectHeader(
                self._parameters,
                len(sections_table),
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
            section_offset += section.physical_size

        self._apply_symbol_tables()
        self._apply_relocation_tables()

    def _apply_symbol_tables(self) -> None:
        """Apply the symbol tables to the sections."""
        for section in self._sections:
            if isinstance(section, SymbolTable):
                self._apply_symbol_table(section)

    def _apply_relocation_tables(self) -> None:
        """Apply the relocation tables to the sections."""
        for section in self._sections:
            if isinstance(section, RelocationTable):
                self._apply_relocation_table(section)

    def _apply_symbol_table(self, table: SymbolTable) -> None:
        """Apply a symbol table to the sections.

        Args:
            table (SymbolTable): The symbol table to apply.
        """
        for section in self._sections:
            self._apply_symbol_table_to_section(table, section)

    def _apply_relocation_table(self, table: RelocationTable) -> None:
        """Apply a relocation table to the sections.

        Args:
            table (RelocationTable): The relocation table to apply.
        """
        for section in self._sections:
            self._apply_relocation_table_to_section(table, section)

    def _apply_symbol_table_to_section(
        self,
        table: SymbolTable,
        section: Section,
    ) -> None:
        """Apply a symbol table to a section.

        Args:
            table (SymbolTable): The symbol table to apply.
            section (Section): The section to apply the symbol table to.
        """
        for symbol in table:
            if symbol.location.section == section.name:
                section.add_symbol(symbol)

    def _apply_relocation_table_to_section(
        self,
        table: RelocationTable,
        section: Section,
    ) -> None:
        """Apply a relocation table to a section.

        Args:
            table (RelocationTable): The relocation table to apply.
            section (Section): The section to apply the relocation table to.
        """
        for relocation in table:
            if relocation.location.section == section.name:
                section.add_relocation(relocation)

    def _section_from_bytes(self, section_type: int, data: bytes, size: int) -> Section:
        if section_type == SectionType.TEXT.value:
            text_section = Text(self._parameters.text_byte)
            text_section.from_bytes(data, size)
            return text_section
        if section_type == SectionType.SYMBOL_TABLE.value:
            symtab_section = SymbolTable()
            symtab_section.from_bytes(data, size)
            return symtab_section
        if section_type == SectionType.RELOCATION_TABLE.value:
            reltab_section = RelocationTable()
            reltab_section.from_bytes(data, size)
            return reltab_section
        raise ValueError(f"Unknown section type: {section_type}")

    def summary(self) -> str:
        """Generate a human-readable summary of the object file.

        Returns:
            str: The summary.
        """
        return (
            f"Object file:\n"
            f"{self._parameters.summary()}"
            f"Sections:\n"
            + "\n".join(self.section_summary(section) for section in self._sections)
        )

    @staticmethod
    def section_summary(section: Section) -> str:
        """Generate a human-readable summary of a section.

        Args:
            section (Section): The section.

        Returns:
            str: The summary.
        """
        return (
            f"  Name: {section.name}\n"
            f"  Size: {len(section)} entries ({section.physical_size} bytes of disk)\n"
        )

    def append_section(self, section: Section) -> None:
        """Append a section to the object file.

        Args:
            section (Section): The section to append.
        """
        for existing_section in self._sections:
            if section.name == existing_section.name:
                existing_section.merge(section)
                return
        self._sections.append(section)

    def merge(self, other: "ObjectManager") -> None:
        """Merge another object file into this one.

        Args:
            other (ObjectFile): The other object file.
        """
        for section in other._sections:
            self.append_section(section)

    def __iter__(self) -> Iterator[Section]:
        """Iterate over the sections.

        Yields:
            Iterator[Section]: The sections.
        """
        return iter(self._sections)
