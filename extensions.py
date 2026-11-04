"""
Flask-SQLAlchemy and Flask-Migrate instances.
Separated to avoid circular imports between app.py and models.py.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

