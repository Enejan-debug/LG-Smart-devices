"""Shared Flask extension instances, kept in their own module to avoid
circular imports between __init__.py, models.py, and the route blueprints."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
