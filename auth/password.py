# auth/password.py - Using sha256_crypt instead of bcrypt
from passlib.context import CryptContext

# Use sha256_crypt which doesn't have the bcrypt compatibility issues
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using sha256_crypt"""
    # Truncate password to 72 characters if needed (though sha256_crypt doesn't have this limit)
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    if len(plain_password) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)