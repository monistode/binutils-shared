"""A set of utilities for working with executables."""
from __future__ import annotations
from dataclasses import dataclass
import mmap
import os
import struct
from typing import Iterator, Protocol

from monistode_binutils_shared.segment import Flags

from .bytearray import ByteArray


@dataclass
class PlacedBinary:
    """A binary that has been placed into memory."""

    data: ByteArray
    offset: int
    size: int
    flags: Flags

    @property
    def disk_size_own_bytes(self) -> int:
        """Get the size of the binary on disk in its own bytes."""
        return len(self.data)

    @property
    def disk_size(self) -> int:
        """Get the size of the binary on disk."""
        return -(-len(self.data) // self.data._byte)

    def __bytes__(self) -> bytes:
        """Return the binary as bytes."""
        return bytes(self.data)

    @classmethod
    def from_bytes(
        cls,
        bytes_: bytes,
        size: int,
        vsize: int,
        offset: int,
        flags: Flags,
        byte_size: int = 8,
    ) -> PlacedBinary:
        """Create a binary from bytes.

        Args:
            bytes_: The bytes to create the binary from.
            size: The size of the binary.
            vsize: The virtual size of the binary.
            offset: The offset of the binary.
            flags: The flags of the binary.
            byte_size: The size of a single byte in the binary.
        """
        array = ByteArray(byte_size, size)
        array.from_bytes(bytes_, size)
        return cls(
            array,
            offset,
            vsize,
            flags,
        )

    def extend(self, other: PlacedBinary, max_extend: int | None = None) -> None:
        """Extend the binary with another binary.

        Args:
            other: The other binary to extend with.
            max_extend: The maximum number of bytes to extend by.
        """
        if len(self.data) < other.offset - self.offset:
            if (
                max_extend is not None
                and other.offset - self.offset - len(self.data) > max_extend
            ):
                raise ValueError(
                    f"Cannot extend binary by {other.offset - len(self.data)} bytes "
                    f"because the maximum extension is {max_extend} bytes"
                )
            self.data.extend([0] * (other.offset - self.offset - len(self.data)))
        if self.data._byte != other.data._byte:
            raise ValueError(
                f"Cannot extend binary with different byte sizes "
                f"({self.data._byte} and {other.data._byte})"
            )
        self.data.extend(other.data)


@dataclass
class SegmentTableEntry:
    """A class representing a segment table entry."""

    start: int
    byte_size: int
    size: int
    vsize: int
    flags: Flags

    def __bytes__(self) -> bytes:
        """Return the segment table entry as bytes."""
        return struct.pack(
            "<IIII",
            self.start,
            self.byte_size,
            self.size,
            self.vsize,
        ) + bytes(self.flags)

    @property
    def segment_disk_size_own_bytes(self) -> int:
        """Get the size of the segment on disk in its own bytes."""
        return self.size

    @property
    def segment_disk_size(self) -> int:
        """Get the size of the segment on disk."""
        return -(-self.size // self.byte_size)

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> "SegmentTableEntry":
        """Return the segment table entry from bytes."""
        (start, byte_size, size, vsize) = struct.unpack(
            "<IIII", bytes_[0 : struct.calcsize("<IIII")]
        )
        return cls(
            start=start,
            byte_size=byte_size,
            size=size,
            vsize=vsize,
            flags=Flags.from_bytes(bytes_[struct.calcsize("<IIII") :]),
        )

    def __len__(self) -> int:
        """Return the length of the segment table entry, in bytes."""
        return struct.calcsize("<III") + len(self.flags)

    @classmethod
    def for_segment(cls, segment: PlacedBinary) -> SegmentTableEntry:
        """Return a segment table entry for a segment.

        Args:
            segment: The segment to create the entry for.
        """
        return cls(
            start=segment.offset,
            byte_size=segment.data._byte,
            size=segment.disk_size_own_bytes,
            vsize=segment.size,
            flags=segment.flags,
        )


@dataclass
class SegmentTable:
    """A class representing a segment table."""

    n_segments: int
    entries: tuple[SegmentTableEntry, ...]

    @classmethod
    def from_bytes(cls, bytes_: bytearray | mmap.mmap, offset: int) -> "SegmentTable":
        """Return the segment table from bytes."""
        n_segments = struct.unpack(
            "<I", bytes_[offset : struct.calcsize("<I") + offset]
        )[0]
        entries: list[SegmentTableEntry] = []
        for i in range(n_segments):
            entry = SegmentTableEntry.from_bytes(
                bytes_[
                    offset
                    + struct.calcsize("<I")
                    + len(SegmentTableEntry) * i : offset
                    + struct.calcsize("<I")
                    + len(SegmentTableEntry) * (i + 1)
                ],
            )
            entries.append(entry)
            offset += entry.segment_disk_size
        return cls(n_segments=n_segments, entries=tuple(entries))

    def __len__(self) -> int:
        """Return the length of the segment table, in bytes."""
        return struct.calcsize("<I") + len(self.entries) * len(SegmentTableEntry)

    def __iter__(self) -> Iterator[SegmentTableEntry]:
        """Return an iterator over the segment table entries."""
        yield from self.entries


@dataclass
class ExecutableHeader:
    """A class representing a binary header."""

    harvard: bool
    entry_point: int
    segment_table: SegmentTable

    def __bytes__(self) -> bytes:
        """Return the binary header as bytes."""
        return struct.pack("<?I", self.harvard, self.entry_point)

    @classmethod
    def from_bytes(cls, bytes_: bytearray | mmap.mmap) -> "ExecutableHeader":
        """Return the binary header from bytes."""
        (harvard, entry_point) = struct.unpack(
            "<?I", bytes_[0 : struct.calcsize("<?I")]
        )
        segment_table = SegmentTable.from_bytes(bytes_, struct.calcsize("<?I"))
        return cls(
            harvard=harvard,
            entry_point=entry_point,
            segment_table=segment_table,
        )

    def __len__(self) -> int:
        """Return the length of the binary header, in bytes."""
        return struct.calcsize("<?I")


class Executable(Protocol):
    """A protocol representing an executable."""

    def clear(
        self,
        harvard: bool,
        entry_point: int,
    ) -> None:
        """Clear the executable."""

    def append_segment(self, segment: PlacedBinary) -> None:
        """Append a segment to the executable."""


@dataclass
class HarvardExecutableFilePair:
    """A folder with yaml files that represent an executable"""

    text: bytearray | mmap.mmap
    data: bytearray | mmap.mmap

    @classmethod
    def from_folder(cls, folder: str) -> "HarvardExecutableFilePair":
        """Return an executable from a folder."""
        text_file = open(os.path.join(folder, "text.bin"), "rb+")
        text = mmap.mmap(text_file.fileno(), 0)
        data_file = open(os.path.join(folder, "data.bin"), "rb+")
        data = mmap.mmap(data_file.fileno(), 0)
        return cls(text=text, data=data)

    def clear(
        self,
        harvard: bool,
        entry_point: int,
    ) -> None:
        """Clear the executable."""
        assert harvard
        assert entry_point == 0
        self.text[0 : len(self.text)] = bytes()
        self.data[0 : len(self.data)] = bytes()

    def append_segment(self, segment: PlacedBinary) -> None:
        if segment.flags.executable:
            self.append_text_segment(segment)
        else:
            self.append_data_segment(segment)

    def append_text_segment(self, segment: PlacedBinary) -> None:
        """Append a segment to the executable."""
        if segment.data:
            self.text_len_to_fit(segment.offset + segment.size)
            self.text[segment.offset : segment.offset + segment.size] = bytes(
                segment.data
            )

    def text_len_to_fit(self, size: int) -> None:
        """Extend the text segment to fit the given size."""
        if size > len(self.text):
            if isinstance(self.text, mmap.mmap):
                self.text.resize(size)
            else:
                self.text.extend(bytes(size - len(self.text)))

    def append_data_segment(self, segment: PlacedBinary) -> None:
        """Append a segment to the executable."""
        if segment.data:
            self.data_len_to_fit(segment.offset + segment.size)
            self.data[segment.offset : segment.offset + segment.size] = bytes(
                segment.data
            )

    def data_len_to_fit(self, size: int) -> None:
        """Extend the data segment to fit the given size."""
        if size > len(self.data):
            if isinstance(self.data, mmap.mmap):
                self.data.resize(size)
            else:
                self.data.extend(bytes(size - len(self.data)))


@dataclass
class ExecutableFile:
    """A class representing an executable."""

    data: bytearray | mmap.mmap

    @property
    def header(self) -> ExecutableHeader:
        """Return the header of the executable."""
        return ExecutableHeader.from_bytes(self.data)

    @classmethod
    def empty(cls, harvard: bool = True) -> bytes:
        """Return an executable with an empty header."""
        return bytes(
            ExecutableHeader(
                harvard=harvard,
                entry_point=0,
                segment_table=SegmentTable(n_segments=0, entries=()),
            )
        )

    def clear(
        self,
        harvard: bool,
        entry_point: int,
    ) -> None:
        """Clear the executable."""
        new_header = ExecutableHeader(
            harvard=harvard,
            entry_point=entry_point,
            segment_table=SegmentTable(n_segments=0, entries=()),
        )
        header_bytes = bytes(new_header)
        self.data[0 : len(header_bytes)] = header_bytes
        if isinstance(self.data, mmap.mmap):
            self.data.resize(len(new_header))

    def segments(self) -> Iterator[PlacedBinary]:
        """Return the segments of the executable."""
        header = self.header
        offset = len(header)
        for binary_entry in header.segment_table:
            binary = PlacedBinary.from_bytes(
                bytes_=self.data[offset : offset + binary_entry.segment_disk_size],
                size=binary_entry.segment_disk_size_own_bytes,
                vsize=binary_entry.vsize,
                offset=binary_entry.start,
                flags=binary_entry.flags,
                byte_size=binary_entry.byte_size,
            )
            yield binary
            offset += binary_entry.size

    def append_segment(self, segment: PlacedBinary) -> None:
        """Append a segment to the executable."""
        entry = SegmentTableEntry.for_segment(segment)
        data_to_append = bytes(entry) + bytes(segment)

        if isinstance(self.data, mmap.mmap):
            size = self.data.size()
            self.data.resize(size + len(data_to_append))
            self.data[size:] = data_to_append
        else:
            self.data += data_to_append

        header = self.header
        header.segment_table.n_segments += 1
        self.data[0 : len(header)] = bytes(header)

    def __len__(self) -> int:
        """Return the length of the executable, in bytes."""
        return len(self.data)
