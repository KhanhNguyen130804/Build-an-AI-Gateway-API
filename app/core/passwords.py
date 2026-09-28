"""Password verification shared by one-off seeding and gateway login."""

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

password_hasher = PasswordHash.recommended()

# Verify unknown usernames against an Argon2id hash too, reducing timing-based
# account enumeration. This value is only a process-local dummy credential.
_DUMMY_PASSWORD_HASH = password_hasher.hash("ai-gateway-invalid-login-placeholder")


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        return password_hasher.verify(password, encoded_hash)
    except UnknownHashError:
        # A malformed/unsupported stored hash must fail closed like a bad password.
        return False


def verify_unknown_user(password: str) -> None:
    password_hasher.verify(password, _DUMMY_PASSWORD_HASH)
