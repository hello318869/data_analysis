import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        plain_password: The raw password string.

    Returns:
        The bcrypt hash as a UTF-8 string.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: The raw password to check.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )
