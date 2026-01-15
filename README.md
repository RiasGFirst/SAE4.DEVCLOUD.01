# SAE4.DEVCLOUD.01 - Application Bancaire

Application bancaire complète développée dans le cadre du projet SAE401, comprenant un backend FastAPI et un frontend Django pour la gestion de comptes bancaires, de transactions et de validations par des agents bancaires.

## 📋 Table des matières

- [Architecture](#architecture)
- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [API Backend](#api-backend)
- [Technologies utilisées](#technologies-utilisées)

## 🏗️ Architecture

Le projet est organisé en architecture microservices avec les composants suivants :

- **Backend** : API REST FastAPI (port 8001)
- **Frontend** : Interface web Django (port 80)
- **Base de données** : MySQL 9.3 (port 3306)
- **Adminer** : Interface d'administration de la base de données (port 8002)

Tous les services sont orchestrés via Docker Compose.

## ✨ Fonctionnalités

### Pour les clients (utilisateurs)
- Authentification et gestion de compte
- Création de comptes (courant, livret)
- Consultation des comptes et soldes
- Opérations bancaires :
  - Dépôts (traités automatiquement)
  - Retraits (nécessitent validation)
  - Virements (nécessitent validation)
- Consultation de l'historique des transactions

### Pour les agents bancaires
- Authentification dédiée
- Validation des comptes en attente
- Validation/refus des transactions (retraits et virements)
- Consultation des logs système
- Gestion des comptes utilisateurs

### Système
- Logging automatique de toutes les requêtes API
- Validation des comptes avant utilisation
- Gestion des transactions atomiques
- Génération automatique d'IBAN (format français)
- Sécurité : mots de passe hashés avec SHA256-Crypt

## 📦 Prérequis

- Docker et Docker Compose
- Git (pour cloner le projet)
- Variables d'environnement configurées (voir section Configuration)

## 🚀 Installation

1. **Cloner le dépôt**
   ```bash
   git clone <url-du-depot>
   cd SAE4.DEVCLOUD.01
   ```

2. **Créer le fichier `.env`** à la racine du projet :
   ```env
   MYSQL_USER=votre_utilisateur
   MYSQL_PASSWORD=votre_mot_de_passe
   MYSQL_DATABASE=nom_de_la_base
   MYSQL_ROOT_PASSWORD=mot_de_passe_root
   ```

3. **Lancer les services avec Docker Compose**
   ```bash
   docker compose up -d
   ```

Les services seront disponibles après quelques instants (attente des health checks).

## ⚙️ Configuration

### Variables d'environnement

Le fichier `.env` doit contenir :
- `MYSQL_USER` : Utilisateur MySQL
- `MYSQL_PASSWORD` : Mot de passe MySQL
- `MYSQL_DATABASE` : Nom de la base de données
- `MYSQL_ROOT_PASSWORD` : Mot de passe root MySQL (optionnel, défaut: CHANGEME)

### Ports exposés

- **80** : Frontend Django (interface web)
- **8001** : Backend FastAPI (API REST)
- **3306** : MySQL (base de données)
- **8002** : Adminer (administration BDD)

### Configuration Backend

Le backend utilise la variable d'environnement `DB_URL` au format :
```
mysql://user:password@db:3306/database
```

Cette variable est automatiquement construite à partir des variables `MYSQL_*` dans le `compose.yml`.

## 💻 Utilisation

### Accès aux interfaces

1. **Interface web** : http://localhost
   - Page d'accueil
   - Authentification clients : `/auth/clients`
   - Authentification banquier : `/auth/banquier`

2. **API Backend** : http://localhost:8001
   - Documentation interactive : http://localhost:8001/docs
   - Endpoint de santé : http://localhost:8001/api/ping

3. **Adminer** : http://localhost:8002
   - Interface d'administration MySQL

### Création d'un compte utilisateur

Via l'API :
```bash
curl -X POST http://localhost:8001/api/user \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "John Doe",
    "email": "john@example.com",
    "mot_de_passe": "motdepasse123",
    "role": "utilisateur"
  }'
```

### Authentification API

L'API utilise l'authentification HTTP Basic :
```bash
curl -u email:motdepasse http://localhost:8001/api/user/me
```

## 📁 Structure du projet

```
SAE4.DEVCLOUD.01/
├── backend/                 # Application FastAPI
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py          # Point d'entrée FastAPI
│   │   ├── models.py        # Modèles de données (Tortoise ORM)
│   │   ├── auth.py          # Authentification HTTP Basic
│   │   ├── settings.py      # Configuration
│   │   └── routes/          # Routes API
│   │       ├── user.py      # Gestion utilisateurs
│   │       ├── account.py   # Gestion comptes
│   │       └── transaction.py # Gestion transactions
│   ├── Dockerfile
│   ├── pyproject.toml       # Dépendances Python (PDM)
│   └── pdm.lock
│
├── frontend/                # Application Django
│   ├── webclient/
│   │   ├── manage.py
│   │   ├── webclient/       # Configuration Django
│   │   └── webinterface/    # Application principale
│   │       ├── models.py
│   │       ├── urls.py
│   │       ├── views/       # Vues (clients, banquier, API)
│   │       ├── templates/  # Templates HTML
│   │       └── static/     # CSS
│   ├── Dockerfile
│   ├── requirements.txt
│   └── start.sh            # Script de démarrage
│
├── compose.yml              # Configuration Docker Compose
├── pyrightconfig.json       # Configuration Pyright
└── README.md
```

## 🔌 API Backend

### Endpoints principaux

#### Utilisateurs (`/api/user`)
- `GET /api/user` : Liste tous les utilisateurs
- `POST /api/user` : Crée un utilisateur
- `GET /api/user/me` : Récupère l'utilisateur connecté
- `GET /api/user/me/recent` : Opérations récentes de l'utilisateur
- `DELETE /api/user/me` : Supprime l'utilisateur connecté

#### Comptes (`/api/account`)
- `GET /api/account` : Liste les comptes de l'utilisateur
- `POST /api/account` : Crée un compte
- `GET /api/account/{account_id}` : Détails d'un compte
- `GET /api/account/tovalidate` : Comptes en attente de validation (agents)
- `POST /api/account/{account_id}/approval` : Valide/refuse un compte (agents)

#### Transactions (`/api/transaction`)
- `POST /api/transaction/{account_id}/depot` : Effectue un dépôt
- `POST /api/transaction/{account_id}/retrait` : Effectue un retrait
- `POST /api/transaction/{account_id}/virement` : Effectue un virement
- `GET /api/transaction/tovalidate` : Transactions en attente (agents)
- `POST /api/transaction/validate/{id}` : Valide/refuse une transaction (agents)

#### Système
- `GET /api/ping` : Vérification de santé
- `GET /api/logs` : Consultation des logs (avec filtres optionnels)

### Modèles de données

- **Utilisateur** : Clients et agents bancaires
- **Compte** : Comptes courants et livrets avec IBAN
- **ValidationCompte** : Validation des comptes par les agents
- **Operation** : Dépôts, retraits, virements
- **Decision** : Décisions de validation des transactions
- **Log** : Journalisation des requêtes API

## 🛠️ Technologies utilisées

### Backend
- **FastAPI** : Framework web asynchrone
- **Tortoise ORM** : ORM asynchrone pour Python
- **MySQL** : Base de données relationnelle
- **Pydantic** : Validation de données
- **Passlib** : Hachage de mots de passe
- **Schwifty** : Génération et validation d'IBAN

### Frontend
- **Django** : Framework web Python
- **Requests** : Client HTTP pour l'API

### Infrastructure
- **Docker** : Conteneurisation
- **Docker Compose** : Orchestration des services
- **Adminer** : Interface d'administration MySQL

### Développement
- **PDM** : Gestionnaire de dépendances Python
- **Python 3.13** : Langage de programmation
- **Pyright** : Analyseur de types statique

## 🔒 Sécurité

- Authentification HTTP Basic pour l'API
- Mots de passe hashés avec SHA256-Crypt
- Validation des comptes avant utilisation
- Vérification des soldes avant transactions
- Transactions atomiques pour garantir la cohérence
- Logging de toutes les requêtes pour audit

## 📝 Notes de développement

- Le backend utilise le mode développement avec rechargement automatique
- Les migrations de base de données sont générées automatiquement au démarrage
- Le frontend crée automatiquement un compte agent bancaire au premier démarrage si nécessaire
- Les dépôts sont traités automatiquement, les retraits et virements nécessitent une validation

## 🐛 Dépannage

### Le backend ne démarre pas
- Vérifier que MySQL est accessible et que les variables d'environnement sont correctes
- Consulter les logs : `docker compose logs backend`

### Le frontend ne peut pas joindre l'API
- Vérifier que `API_HOST` est correctement configuré dans `compose.yml`
- Vérifier que le backend répond : `curl http://localhost:8001/api/ping`

### Problèmes de base de données
- Utiliser Adminer (http://localhost:8002) pour inspecter la base
- Vérifier les health checks : `docker compose ps`

## 📄 Licence

Aucune licence spécifiée.

## 👥 Auteurs

- RiasGFirst (FrontEnd)
- Sutaai (BackEnd)

---

**Projet SAE401** - Application bancaire avec gestion de comptes et transactions
