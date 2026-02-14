"""
Simple password hashing utilities.

This implementation avoids external dependencies so Pyright and runtime
environments don't require `passlib`. For production you would typically
use a stronger hashing library like `passlib` or `argon2-cffi`.
"""

from __future__ import annotations

import hashlib
import os
from typing import Final


_SALT_BYTES: Final[int] = 16


def _hash_with_salt(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + digest.hex()


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a random salt.
    """
    salt = os.urandom(_SALT_BYTES)
    return _hash_with_salt(password, salt)


def verify_password(password: str, stored: str) -> bool:
    """
    Verify a password against a stored hash (salt:digest hex).
    """
    try:
        salt_hex, _ = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        return _hash_with_salt(password, salt) == stored
    except (ValueError, TypeError):
        return False
