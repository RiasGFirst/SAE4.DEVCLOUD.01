from django.shortcuts import render, redirect
from django.contrib import messages  # 👈 important
import dotenv
import requests
import os

# Load environment variables from .env file
dotenv.load_dotenv()
DJANGO_HOST = os.getenv('URL_DJANGO')


def auth_page(request):
    if request.method == "POST":
        if "register" in request.POST:
            username = request.POST.get("username")
            email = request.POST.get("email")
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")

            if password1 == password2:
                # Ici tu peux appeler une API pour l’enregistrement ou créer l’utilisateur
                response = requests.post(f"{DJANGO_HOST}/api/create_account", data={
                    'username': username,
                    'email': email,
                    'password': password1
                })
                if response.ok:
                    data = response.json()
                    print(data)
                    messages.success(request, f"L'utilisateur {data['nom']} a été inscrit avec succès.")
                else:
                    try:
                        error_msg = response.json().get('error', 'Erreur inconnue')
                    except Exception as e:
                        print("Erreur JSON :", e)
                        error_msg = response.text  # pour affichage debug si HTML
                    messages.error(request, f"Échec de l'inscription : {error_msg}")
                #messages.success(request, f"L'utilisateur {username} a été inscrit avec succès.")
                return redirect('/auth/clients')  # 👈 redirection après succès pour éviter double POST
            else:
                messages.error(request, "Les mots de passe ne correspondent pas. Réessaie.")
                return redirect('/auth/clients')

        elif "login" in request.POST:
            username = request.POST.get("email")
            password = request.POST.get("password")

            # Authentifie avec une API ou ton système
            if username and password:
                response = requests.post(f"{DJANGO_HOST}/api/connect_client", data={
                    'username': username,
                    'password': password
                })
                if response.ok:
                    data = response.json()
                    print(data)
                    # Création de la réponse de redirection
                    response = redirect('/clients/dashboard')
                    # On met le username et le password dans des cookies (attention à la sécurité)
                    response.set_cookie('username', username, max_age=7*24*3600)  # 7 jours
                    response.set_cookie('password', password, max_age=7*24*3600)  # 7 jours
                    return response  # 👈 redirection vers le dashboard client
                else:
                    try:
                        error_msg = response.json().get('error')
                    except Exception as e:
                        print("Erreur JSON :", e)
                        error_msg = response.text
                    messages.error(request, f"Échec de la connexion : {error_msg}")
                return redirect('/auth/clients')
            else:
                messages.error(request, "Identifiants invalides. Merci de réessayer.")
                return redirect('/auth/clients')

    return render(request, 'clients/auth.html')


def dashboard_client(request):
    # ⚠️ Ces données sont simulées. À remplacer par un appel API ou une requête BDD.

    # Exemple de données de comptes pour le client
    comptes = [
        {'type': 'Compte courant', 'numero': 'XXXX-XXXX-XXXX', 'solde': 1250.45},
        {'type': 'Livret A', 'numero': 'YYYY-YYYY-YYYY', 'solde': 3400.00},
        {'type': 'PEL', 'numero': 'ZZZZ-ZZZZ-ZZZZ', 'solde': 7800.50}
    ]

    nom_client = "Jean Dupont"  # ⚠️ À remplacer par la récupération via session, user connecté, ou API

    return render(request, 'clients/dashboard.html', {
        'comptes': comptes,
        'nom_client': nom_client
    })