import hashlib
import secrets
import os

def hash_password(password):
    """Hash a password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, hashed_password):
    """Verify a password against its hash."""
    try:
        salt, password_hash = hashed_password.split(':')
        computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return computed_hash == password_hash
    except ValueError:
        return False

def generate_secret_key():
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)

def get_secure_config():
    """Get secure configuration values."""
    return {
        'SECRET_KEY': os.environ.get('SECRET_KEY', generate_secret_key()),
        'DB_ADMIN_USERNAME': os.environ.get('DB_ADMIN_USERNAME', 'admin'),
        'DB_ADMIN_PASSWORD': os.environ.get('DB_ADMIN_PASSWORD', 'tcfadmin2024'),
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'development')
    }
