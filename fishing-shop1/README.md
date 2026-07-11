# Клюй Bait — магазин прикормок

Простий лендінг + каталог + адмін-панель + замовлення в Telegram.

## Швидкий старт (Windows)

```powershell
cd c:\Users\Artem\Documents\new\fishing-shop
copy .env.example .env
py -m pip install -r requirements.txt
py app.py
```

Відкрий: http://127.0.0.1:5000  
Адмін: http://127.0.0.1:5000/admin (логін `admin`, пароль з `.env`)

## Налаштування `.env`

```
TELEGRAM_USERNAME=твій_нік
SHOP_NAME=Твоя назва
ADMIN_PASSWORD=надійний_пароль
SECRET_KEY=випадковий_рядок
SITE_URL=https://твій-домен.com
```

## Адмін-панель

- **Товари** — додати / редагувати / видалити
- **Категорії** — свої розділи (прикормки, ароматизатори, добавки…)
- Фото, ціна, фасування, порядок, «Популярне»
- На телефоні — зручне меню знизу

Адмін: http://127.0.0.1:5000/admin

## Хостинг

### Shared-хостинг з cPanel "Setup Python App" (hostiq.ua, imena.ua, ehost.ua тощо)

Це найпоширеніший варіант в Україні. Панель сама створює свій `passenger_wsgi.py` —
**заміни його файлом з цього проєкту**, інакше вона не побачить твій Flask-застосунок.

1. У cPanel відкрий "Setup Python App", створи застосунок (обери версію Python 3.10+)
2. Панель покаже шлях (напр. `/home/USER/fishing-shop`) і віртуальне середовище
3. Залий туди всі файли проєкту **крім** `__pycache__`
4. У полі **Application startup file**: `passenger_wsgi.py`
5. У полі **Application Entry point**: `application`
6. Через кнопку "Run Pip Install" встанови залежності з `requirements.txt`
   (або в Terminal панелі: `pip install -r requirements.txt`)
7. Онови `.env` під реальні дані (домен, телеграм-нік, пароль адмінки)
8. Натисни "Restart"

### PythonAnywhere

1. Завантаж папку `fishing-shop` на акаунт
2. Створи virtualenv, `pip install -r requirements.txt`
3. У Web → WSGI file: `wsgi.py`
4. Додай `.env` або змінні в панелі
5. Static files: `/static/` → `fishing-shop/static/`

### VPS (Ubuntu + gunicorn + nginx)

```bash
pip install -r requirements.txt gunicorn
gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app
```

Nginx проксує на порт 8000, SSL через Certbot.

### Що завантажити на хостинг

- Усі файли крім `__pycache__` та `*.pyc` (стара компіляція під іншу версію
  Python на твоєму ПК могла заважати серверу — видали перед заливкою)
- `.env` заповни ПОВНІСТЮ: `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`,
  `TELEGRAM_USERNAME`, `SITE_URL` — якщо чогось нема, підставляться небезпечні
  дефолти (пароль адмінки `admin123`, замовлення підуть не на твій телеграм)
- Папка `static/uploads/` — права на запис (фото товарів)
- Файл `store.db` створиться сам, або скопіюй з локального

## Логотип

Коли буде лого — поклади в `static/img/logo.png` і скажи — підключимо в шапку.

## Перезапуск сервера

У терміналі **Ctrl+C**, потім знову:

```powershell
py app.py
```
