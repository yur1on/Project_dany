# Сайт автомастерской на Django

Небольшой сайт для автосервиса AVTOMOD: главная страница, список услуг, форма заявки, контакты и админка для управления услугами и заявками.

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

После запуска сайт будет доступен на `http://127.0.0.1:8000/`, админка - на `http://127.0.0.1:8000/admin/`.

## Telegram-уведомления

Чтобы заявки приходили в Telegram, перед запуском сервера задайте переменные:

```bash
export TELEGRAM_BOT_TOKEN="токен_бота"
export TELEGRAM_CHAT_ID="id_чата"
python manage.py runserver
```

Если переменные не заданы, заявки просто сохраняются в админке без отправки в Telegram.

## Проверка

```bash
python manage.py test
```
