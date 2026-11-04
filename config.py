import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def normalize_db_url(url: str) -> str:
    """Normalize database connection string and encode special chars in password."""
    if not url:
        return "sqlite:///student_management.db"
    
    # Handle Heroku / Supabase legacy scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Automatically URL-encode password if it contains '@'
    if "://" in url and "@" in url:
        scheme, rest = url.split("://", 1)
        last_at_idx = rest.rfind("@")
        auth_part = rest[:last_at_idx]
        host_part = rest[last_at_idx + 1:]
        if ":" in auth_part:
            user, password = auth_part.split(":", 1)
            # Encode any raw '@' in the password
            if "@" in password:
                password = password.replace("@", "%40")
            url = f"{scheme}://{user}:{password}@{host_part}"

    # Ensure psycopg2 driver is explicitly used
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    return url


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    _raw_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/student_management"
    )
    SQLALCHEMY_DATABASE_URI = normalize_db_url(_raw_url)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration — uses a separate test DB (PostgreSQL or SQLite fallback)."""
    TESTING = True
    _raw_test_url = os.environ.get(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:"
    )
    if _raw_test_url.startswith("postgres://"):
        _raw_test_url = _raw_test_url.replace("postgres://", "postgresql://", 1)
    if _raw_test_url.startswith("postgresql://") and "+psycopg2" not in _raw_test_url:
        _raw_test_url = _raw_test_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    SQLALCHEMY_DATABASE_URI = _raw_test_url
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
