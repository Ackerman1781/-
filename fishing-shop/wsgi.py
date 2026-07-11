"""Точка входу для хостингу (PythonAnywhere, Passenger, gunicorn)."""
from app import app, ensure_default_social
from database import init_db

init_db()
ensure_default_social()