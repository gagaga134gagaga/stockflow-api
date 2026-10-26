FROM python:3.12-slim

# Не создаём .pyc-файлы и сразу выводим логи в терминал.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем основные зависимости и инструменты разработки.
# Копируем их отдельно, чтобы Docker кешировал установку пакетов.
COPY requirements.txt requirements-dev.txt ./

RUN pip install --no-cache-dir -r requirements-dev.txt

# Копируем исходный код приложения.
COPY . .

# Проверяем синтаксис Python-файлов при сборке.
RUN python -m compileall -q .

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]