FROM python:3.13-slim

WORKDIR /bot

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

COPY app/ ./
COPY config.ini ./
COPY i18n.toml ./
COPY locales ./
COPY resources ./
COPY . .

COPY pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install --no-root

CMD ["python3", "-m", "app"]

