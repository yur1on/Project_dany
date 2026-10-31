# Прототип AVTOMOD

Это отдельный статический прототип, не подключенный к данным Django. Тексты и фотография взяты из локального проекта и не обновляются автоматически.

Запуск:

```bash
cd /Users/yura/Documents/auto_repair/prototype
npm install
npm run dev
```

По умолчанию ссылки на услуги, галерею и форму звонка ведут на Django по адресу `http://127.0.0.1:8015`. Если Django запущен на другом порту, укажите его при запуске Vite:

```bash
VITE_DJANGO_URL=http://127.0.0.1:8002 npm run dev
```

Чтобы запустить Django отдельно:

```bash
cd /Users/yura/Documents/auto_repair
source .venv/bin/activate
python manage.py runserver 8015
```
