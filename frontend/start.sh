#!/bin/bash

AUTH_FILE="accounts.txt"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

generate_random() {
    tr -dc 'a-zA-Z0-9' </dev/urandom | head -c "$1"
}

# load_env() {
#     if [ -f ".env" ]; then
#         echo "${GREEN}✔️ Chargement des variables d'environnement...${NC}"
#         export $(grep -v '^#' .env | xargs)
#     else
#         echo -e "${RED}❌ Fichier .env introuvable.${NC}"
#         exit 1
#     fi
# }

check_api() {
    if [ -z "$API_HOST" ]; then
        echo -e "${RED}❌ API_HOST n'est pas défini.${NC}"
        exit 1
    fi
    echo -e "${YELLOW}🔍 Vérification API à $API_HOST...${NC}"
    response=$(curl -s "$API_HOST/api/ping")
    if [ "$response" == '"pong"' ]; then
        echo -e "${GREEN}✔️ API accessible.${NC}"
    else
        echo -e "${RED}❌ API inaccessible.${NC}"
        exit 1
    fi
}

run_django() {
    echo -e "${GREEN}🚀 Démarrage du serveur Django...${NC}"
    
    echo "USER: $(grep 'username:' "$AUTH_FILE" | cut -d ' ' -f2)"
    echo "EMAIL: $(grep 'email:' "$AUTH_FILE" | cut -d ' ' -f2)"
    echo "PASSWORD: $(grep 'mdp:' "$AUTH_FILE" | cut -d ' ' -f2)"

    python webclient/manage.py runserver 0.0.0.0:8000
}

# load_env
check_api

if [ -f "$AUTH_FILE" ]; then
    echo -e "${GREEN}✔️ $AUTH_FILE trouvé.${NC}"
    run_django
else
    echo -e "${YELLOW}⚠️ $AUTH_FILE manquant. Création...${NC}"
    USERNAME="user_$(generate_random 6)"
    EMAIL="${USERNAME}@example.com"
    PASSWORD="$(generate_random 12)"
    echo "username: $USERNAME" > "$AUTH_FILE"
    echo "email: $EMAIL" >> "$AUTH_FILE"
    echo "mdp: $PASSWORD" >> "$AUTH_FILE"

    curl -s -X POST "$API_HOST/api/user" \
         -H "Content-Type: application/json" \
         -d '{
             "nom": "'"$USERNAME"'",
             "email": "'"$EMAIL"'",
             "mot_de_passe": "'"$PASSWORD"'",
             "role": "agent_bancaire"
         }'

    echo -e "${GREEN}✔️ Identifiants créés et envoyés.${NC}"
    run_django
fi
