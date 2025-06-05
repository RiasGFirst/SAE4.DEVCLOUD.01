FROM python:3.13

WORKDIR /app

COPY pyproject.toml .
COPY pdm.lock .

RUN pip install .

COPY backend/ ./backend/

<<<<<<< HEAD
CMD ["fastapi", "run", "/app/backend"]
=======
# TODO: Changer en "run" une fois le développement terminé
CMD ["fastapi", "dev", "/app/backend"]
>>>>>>> origin/main
