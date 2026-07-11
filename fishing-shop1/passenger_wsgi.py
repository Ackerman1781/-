"""
Точка входу для хостингів на Passenger (cPanel -> Setup Python App).
Більшість українських shared-хостингів (hostiq.ua, imena.ua, ehost.ua тощо)
для Python-застосунків шукають САМЕ файл passenger_wsgi.py
зі змінною application всередині.

Якщо твій хостинг використовує cPanel "Setup Python App":
1. Завантаж усі файли проєкту в папку, яку вкаже панель
   (зазвичай там уже буде свій passenger_wsgi.py — заміни його цим)
2. У полі "Application startup file" вкажи: passenger_wsgi.py
3. У полі "Application Entry point" вкажи: application
4. Встанови залежності через кнопку в панелі або
   у Terminal: pip install -r requirements.txt
"""
import sys
import os

# Додаємо папку проєкту в шлях пошуку модулів
sys.path.insert(0, os.path.dirname(__file__))

from app import app, ensure_default_social
from database import init_db

init_db()
ensure_default_social()

application = app
