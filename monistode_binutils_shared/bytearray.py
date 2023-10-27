"""A class representing a bytearray of any esoteric byte size."""

from typing import Iterable, Iterator

import bitstruct


class ByteArray:
    """A class representing a bytearray of any esoteric byte size."""

    def __init__(self, byte: int, capacity: int = 0) -> None:
        """Initialize the bytearray.

        Args:
            byte (int): The byte to start at.
            capacity (int): The initial capacity of the bytearray. Defaults to 0.
        """
        self._byte = byte
        self._data = bytearray(-(-capacity * byte // 8))
        self._format = f"u{byte}"
        self._length: int = 0
        self._capacity = capacity

    def __getitem__(self, index: int) -> int:
        """Get the byte at the given index.

        Args:
            index (int): The index of the byte.

        Returns:
            int: The byte at the given index.
        """
        if index >= self._length:
            raise IndexError("Index out of range")
        return bitstruct.unpack_from(self._format, self._data, index * self._byte)[0]

    def __setitem__(self, index: int, value: int) -> None:
        """Set the byte at the given index.

        Args:
            index (int): The index of the byte.
            value (int): The value to set the byte to.
        """
        if index >= self._length:
            raise IndexError("Index out of range")
        bitstruct.pack_into(self._format, self._data, index * self._byte, value)

    def __len__(self) -> int:
        """Get the length of the bytearray.

        Returns:
            int: The length of the bytearray.
        """
        return self._length

    def __iter__(self) -> Iterator[int]:
        """Get an iterator for the bytearray.

        Returns:
            int: An iterator for the bytearray.
        """
        for i in range(self._length):
            yield self[i]

    def append(self, value: int) -> None:
        """Append a byte to the bytearray.

        Args:
            value (int): The byte to append.
        """
        self._length += 1
        if self._length >= self._capacity:
            if self._capacity == 0:
                self._capacity = 1
            self._capacity *= 2
            self._data.extend(bytearray(-(-self._capacity * self._byte // 8)))
        self[self._length - 1] = value

    def to_bytes(self) -> bytes:
        """Convert the bytearray to a bytes object.

        Returns:
            bytes: The bytearray as a bytes object.
        """
        return bytes(self._data[: -(-self._length * self._byte // 8)])

    def __bytes__(self) -> bytes:
        """Convert the bytearray to a bytes object.

        Returns:
            bytes: The bytearray as a bytes object.
        """
        return self.to_bytes()

    def from_bytes(self, data: bytes, length: int) -> None:
        """Convert a bytes object to a bytearray.

        Args:
            data (bytes): The bytes object to convert.
            length (int): The length of the bytearray.
        """
        self._data = bytearray(data)
        self._length = length
        self._capacity = length

    def extend(self, data: Iterable[int]) -> None:
        """Extend the bytearray with an iterable.

        Args:
            data (Iterable[int]): The iterable to extend the bytearray with.
        """
        for byte in data:
            self.append(byte)

    def clear(self) -> None:
        """Clear the bytearray."""
        self._length = 0
