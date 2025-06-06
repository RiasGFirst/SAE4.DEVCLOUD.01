# Pour info: On a besoin de GCC donc pas d'Alpine malheureusement
FROM python:3.13

WORKDIR /app

COPY pyproject.toml .
COPY pdm.lock .

RUN pip install .

COPY backend/ ./backend/

CMD ["fastapi", "run", "/app/backend", "--reload"]
