from __future__ import annotations

from hashlib import sha1


class HashFunction:
    """
    Stable, deterministic hash for ring placement.
    Uses SHA-1 and truncates to 32-bit unsigned (0 .. 2^32-1).
    """

    RING_BITS = 32
    RING_SIZE = 2 ** RING_BITS

    @staticmethod
    def hash32(data: str) -> int:
        digest = sha1(data.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], byteorder="big", signed=False)
