FROM python:3.11-slim

WORKDIR /bot

COPY app/ ./
COPY config.ini ./
COPY i18n.toml ./
COPY locales ./
COPY resources ./
COPY . .

RUN pip install --no-cache-dir aiocache aiohttp redis aiogram configparser hermes-langlib rich loguru pytz

CMD ["python3", "-m", "app"]

