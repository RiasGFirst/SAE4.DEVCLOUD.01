FROM python:3.13

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY pdm.lock .

RUN pip install .

COPY backend/ ./backend/

CMD ["fastapi", "run", "/app/backend", "--reload"]
