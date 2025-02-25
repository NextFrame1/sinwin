FROM python:3.13-slim

WORKDIR /bot

COPY app/ ./
COPY config.ini ./
COPY i18n.toml ./
COPY locales ./
COPY resources ./
COPY . .

RUN pip install --no-cache-dir apscheduler python-dateutil aiocache aiohttp redis aiogram configparser hermes-langlib rich loguru pytz

CMD ["python3", "-m", "app"]

