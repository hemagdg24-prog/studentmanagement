import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    # Force psycopg2 dialect so SQLAlchemy 2.x doesn't try to import psycopg3
    _raw_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/student_management"
    )
    # Normalise Supabase / Railway URLs that use "postgres://" scheme
    if _raw_url.startswith("postgres://"):
        _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)
    # Ensure the psycopg2 driver is specified
    if _raw_url.startswith("postgresql://") and "+psycopg2" not in _raw_url:
        _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    SQLALCHEMY_DATABASE_URI = _raw_url
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
