FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install poetry==1.8.2

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev deps, no virtualenv inside container)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy application code, migrations, and seed script
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY seed.py ./
COPY start.sh ./
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
