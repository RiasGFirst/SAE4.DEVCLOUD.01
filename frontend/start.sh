#!/bin/bash

# Chemin vers le fichier d'authentification
AUTH_FILE="bauth.txt"

# Fonction pour générer une chaîne aléatoire
generate_random() {
    tr -dc 'a-zA-Z0-9' </dev/urandom | head -c "$1"
}

# Charger les variables du fichier .env s'il existe
load_env() {
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    else
        echo "❌ Fichier .env introuvable."
        exit 1
    fi
}

# Activer l'environnement virtuel
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "Environnement virtuel non trouvé. Création..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
}

# Lancer Django
run_django() {
    echo "Lancement du serveur Django..."
    python webclient/manage.py runserver 0.0.0.0:8000
}


# Charger les variables .env
load_env

# Vérifie si le fichier bauth.txt existe
if [ -f "$AUTH_FILE" ]; then
    echo "Fichier $AUTH_FILE trouvé."
    activate_venv
    run_django
else
    echo "Fichier $AUTH_FILE manquant. Création d'identifiants..."

    USERNAME="user_$(generate_random 6)"
    EMAIL="${USERNAME}@example.com"
    PASSWORD="$(generate_random 12)"

    echo "username: $USERNAME" > "$AUTH_FILE"
    echo "email: $EMAIL" >> "$AUTH_FILE"
    echo "mdp: $PASSWORD" >> "$AUTH_FILE"

    # Vérifie que API_HOST est défini
    if [ -z "$API_HOST" ]; then
        echo "❌ API_HOST n'est pas défini dans le .env."
        exit 1
    fi

    # faire une requête POST pour enregistrer les identifiants
    echo "Enregistrement des identifiants dans l'API..."
    curl -X POST "$API_HOST/api/user/" \
        -H "Content-Type: application/json" \
        -d '{
            "nom": "'"$USERNAME"'",
            "email": "'"$EMAIL"'",
            "mot_de_passe": "'"$PASSWORD"'",
            "role": "agent_bancaire"
        }'


    echo "Identifiants enregistrés dans $AUTH_FILE"
    activate_venv
    run_django
fi
