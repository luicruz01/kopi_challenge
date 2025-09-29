"""Utility functions for deterministic operations."""
import hashlib
import subprocess
from pathlib import Path


def get_git_hash() -> str | None:
    """Get the current git commit hash."""
    try:
        # Check if we're in a git repository
        git_dir = Path(".git")
        if not git_dir.exists():
            # Try to find .git in parent directories
            current_dir = Path.cwd()
            while current_dir != current_dir.parent:
                git_dir = current_dir / ".git"
                if git_dir.exists():
                    break
                current_dir = current_dir.parent
            else:
                return None

        # Get the current commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0:
            return result.stdout.strip()[:8]  # Return short hash (8 chars)
        else:
            return None

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return None


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
