"""Точка входу для хостингу (PythonAnywhere, gunicorn)."""
from app import app, ensure_default_social
from database import init_db

init_db()
ensure_default_social()

# gunicorn запускається як `gunicorn wsgi:app`
# PythonAnywhere у полі WSGI file теж шукає змінну `application`
application = app