"""
Password hashing via PBKDF2-HMAC-SHA256 (stdlib `hashlib`, no compiled deps).

The original project had no authentication at all -- anyone could open the
app and see or edit any patient's data. Real hospital software is bound by
confidentiality requirements (e.g. HIPAA in the US, IT Act/DPDP in India), so
role-based login is treated here as a baseline requirement, not a nice-to-have.
"""
import hashlib
import os
import secrets

_ITERATIONS = 200_000


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Returns (hash_hex, salt_hex). Generates a new random salt if none given."""
    if salt is None:
        salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
    )
    return derived.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(password, salt)
    return secrets.compare_digest(candidate, password_hash)
