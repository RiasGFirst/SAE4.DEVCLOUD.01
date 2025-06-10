#!/bin/bash

# Chemin vers le fichier d'authentification
AUTH_FILE="bauth.txt"

# Codes de couleur
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour générer une chaîne aléatoire
generate_random() {
    tr -dc 'a-zA-Z0-9' </dev/urandom | head -c "$1"
}

# Charger les variables du fichier .env s'il existe
load_env() {
    if [ -f ".env" ]; then
        echo "${GREEN} ✔️ Chargement des variables d'environnement depuis .env ${NC}"
        export $(grep -v '^#' .env | xargs)
    else
        echo -e "${RED}❌ Fichier .env introuvable.${NC}"
        exit 1
    fi
}

# Activer l'environnement virtuel
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        echo -e "${GREEN}✔️ Environnement virtuel trouvé. Activation...${NC}"
        source venv/bin/activate
    else
        echo -e "${RED}❌ Environnement virtuel non trouvé. Création...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
}

# Vérifier si l'API est accessible et répond "pong"
check_api() {
    if [ -z "$API_HOST" ]; then
        echo -e "${RED}❌API_HOST n'est pas défini dans le .env.${NC}"
        exit 1
    fi

    echo -e "${YELLOW}🔍Vérification de l'API à l'adresse $API_HOST...${NC}"

    # Faire une requête GET à l'API et vérifier la réponse
    response=$(curl -s "$API_HOST/api/ping")
    if [ "$response" == '"pong"' ]; then
        echo -e "${GREEN}✔️ API est accessible.${NC}"
    else
        echo -e "${RED}❌API n'est pas accessible. Veuillez vérifier l'URL.${NC}"
        exit 1
    fi
}


# Lancer Django
run_django() {
    echo -e "${GREEN}🚀Démarrage du serveur Django...${NC}"
    python webclient/manage.py runserver 0.0.0.0:8000
}


# Charger les variables .env
load_env

# Vérifier si l'API est accessible
check_api

# Vérifie si le fichier bauth.txt existe
if [ -f "$AUTH_FILE" ]; then
    echo -e "${GREEN}✔️ Fichier $AUTH_FILE trouvé.${NC}"
    activate_venv
    run_django
else
    echo -e "${YELLOW}⚠️ Fichier $AUTH_FILE introuvable. Création de nouveaux identifiants...${NC}"

    USERNAME="user_$(generate_random 6)"
    EMAIL="${USERNAME}@example.com"
    PASSWORD="$(generate_random 12)"

    echo "username: $USERNAME" > "$AUTH_FILE"
    echo "email: $EMAIL" >> "$AUTH_FILE"
    echo "mdp: $PASSWORD" >> "$AUTH_FILE"

    # faire une requête POST pour enregistrer les identifiants
    echo -e "${YELLOW}⚙️ Enregistrement des identifiants dans l'API...${NC}"
    curl -s -X POST "$API_HOST/api/user/" \
            -H "Content-Type: application/json" \
            -d '{
                "nom": "'"$USERNAME"'",
                "email": "'"$EMAIL"'",
                "mot_de_passe": "'"$PASSWORD"'",
                "role": "agent_bancaire"
            }' > /dev/null

    echo -e "${GREEN}✔️ Identifiants enregistrés avec succès.${NC}"
    echo -e "${YELLOW}⚙️ Activation de l'environnement virtuel et démarrage de Django...${NC}"
    activate_venv
    run_django
fi
