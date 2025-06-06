from django.shortcuts import render, redirect
from django.contrib import messages  # 👈 important
from dotenv import load_dotenv
import requests
import os

# Load environment variables from .env file
load_dotenv()
DJANGO_HOST = os.getenv('URL_DJANGO')


def auth_page(request):
    if request.method == "POST":
        if "login" in request.POST:
            username = request.POST.get("username")
            password = request.POST.get("password")

            # Authentifie avec une API ou ton système
            if username and password:
                response = requests.post(f"{DJANGO_HOST}/api/connect_banquier", data={
                    'username': username,
                    'password': password
                })
                if response.ok:
                    data = response.json()
                    print(data)
                    # Création de la réponse de redirection
                    rdirect = redirect('dashboard_manager')
                    # On met le username et le password dans des cookies (attention à la sécurité)
                    rdirect.set_cookie('busername', username, max_age=7*24*3600)
                    rdirect.set_cookie('bpassword', password, max_age=7*24*3600)
                    rdirect.set_cookie('buser', data.get('nom'), max_age=7*24*3600)
                    return rdirect
                else:
                    try:
                        error_msg = response.json().get('error', 'Erreur inconnue')
                    except Exception as e:
                        print("Erreur JSON :", e)
                        error_msg = response.text
                    print("Authentication failed:", response.status_code, error_msg)
                    messages.error(request, f"Échec de l'authentification : {error_msg}")
                    return redirect('auth_banquier_page')
            else:
                print("Username or password not provided.")
                messages.error(request, error_msg)
                return redirect('auth_banquier_page')
    else:
        # Si la méthode n'est pas POST, on affiche simplement la page d'authentification
        if request.COOKIES.get('busername') and request.COOKIES.get('bpassword'):
            # Si l'utilisateur est déjà connecté, on le redirige vers le tableau de bord
            return redirect('dashboard_manager')


    return render(request, 'banquier/auth.html')

def manager_dashboard(request):
    # Vérifie si l'utilisateur est connecté
    if not request.COOKIES.get('busername') or not request.COOKIES.get('bpassword'):
        messages.error(request, "Vous devez vous connecter pour accéder au tableau de bord.")
        return redirect('auth_banquier_page')
    # Liste simulée de transactions
    transactions = [
        {
            'id': 1,
            'type': 'Virement',
            'expediteur': 'Jean Dupont',
            'beneficiaire': 'Marie Durand',
            'montant': 250.00,
            'date': '2025-06-01'
        },
        {
            'id': 2,
            'type': 'Retrait',
            'expediteur': 'Sophie Martin',
            'beneficiaire': None,
            'montant': 100.00,
            'date': '2025-06-02'
        },
        {
            'id': 3,
            'type': 'Virement',
            'expediteur': 'Paul Morel',
            'beneficiaire': 'Lucie Leroy',
            'montant': 400.00,
            'date': '2025-06-03'
        }
    ]

    context = {
        'transactions': transactions,
        'nom_manager': request.COOKIES.get('buser', 'Manager inconnu'),
    }

    return render(request, 'banquier/dashboard.html', context)


def logout(request):
    # Supprime les cookies de session
    response = redirect('auth_banquier_page')
    response.delete_cookie('busername')
    response.delete_cookie('bpassword')
    response.delete_cookie('buser')
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return response