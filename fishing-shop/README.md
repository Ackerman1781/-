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

### PythonAnywhere (простий варіант)

1. Завантаж папку `fishing-shop` на акаунт
2. Створи virtualenv, `pip install -r requirements.txt`
3. У Web → WSGI вкажи `wsgi.py`
4. Додай `.env` або змінні в панелі
5. Static files: `/static/` → `fishing-shop/static/`

### VPS (Ubuntu + gunicorn + nginx)

```bash
pip install -r requirements.txt gunicorn
gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app
```

Nginx проксує на порт 8000, SSL через Certbot.

### Що завантажити на хостинг

- Усі файли крім `__pycache__`, `.env` (створи на сервері)
- Папка `static/uploads/` — права на запис (фото товарів)
- Файл `store.db` створиться сам, або скопіюй з локального

## Логотип

Коли буде лого — поклади в `static/img/logo.png` і скажи — підключимо в шапку.

## Перезапуск сервера

У терміналі **Ctrl+C**, потім знову:

```powershell
py app.py
```
