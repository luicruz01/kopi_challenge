"""Utility functions for deterministic operations."""
import hashlib


def stable_index(key: str, mod: int, *, salt: str = "") -> int:
    """
    Generate a stable index for deterministic selection.

    Args:
        key: String key to hash
        mod: Modulo value (list/array length)
        salt: Optional salt for additional randomization

    Returns:
        Stable index in range [0, mod)
    """
    h = hashlib.sha256((salt + key).encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") % max(1, mod)
