FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && \
    apt-get install -y curl gcc libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Installer les dépendances
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copier tous les fichiers
COPY . .

# Donner les droits d'exécution au script
RUN chmod +x start.sh

# Commande de démarrage
CMD ["./start.sh"]
