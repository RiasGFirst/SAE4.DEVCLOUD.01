from django.shortcuts import render, redirect
from django.contrib import messages  # 👈 important
import requests
import dotenv
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
                    messages.success(request, f"L'utilisateur {username} a été inscrit avec succès.")
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
                    response.set_cookie('user', data.get('nom'), max_age=7*24*3600)  # 7 jours
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
    else:
        # Si la méthode n'est pas POST, on affiche simplement la page d'authentification
        if request.COOKIES.get('username') and request.COOKIES.get('password'):
            # Si l'utilisateur est déjà connecté, on le redirige vers le tableau de bord
            return redirect('/clients/dashboard')

    return render(request, 'clients/auth.html')


def dashboard_client(request):
    # ⚠️ Ces données sont simulées. À remplacer par un appel API ou une requête BDD.
    if not request.COOKIES.get('username') or not request.COOKIES.get('password'):
        messages.error(request, "Veuillez vous connecter d'abord.")
        return redirect('/auth/clients')
    
    nom_client = request.COOKIES.get('user', 'Client inconnu')
    print("Nom du client récupéré depuis les cookies :", nom_client)  # Pour debug

    # Récupération des comptes via l'API
    response = requests.post(f"{DJANGO_HOST}/api/get_accounts",
                            data={
                                'username': request.COOKIES.get('username'),
                                'password': request.COOKIES.get('password')
                            })
    if response.ok:
        comptes_data = response.json()
        print("Comptes récupérés :", comptes_data)  # Pour debug
        comptes = []
        for compte in comptes_data:
            compte_type = compte.get('type_compte', 'N/A')  # Assurez-vous que le type de compte est défini
            comptes_type = {
                'compte_courant': 'Compte courant',
                'livret': 'Livret A',
            }

            compte['type'] = comptes_type[compte_type]  # Assurez-vous que le type de compte est défini
            compte['numero'] = compte.get('id', 'N/A')
            compte['solde'] = float(compte.get('solde', 0.0))  # Assurez-vous que le solde est un float
            compte['validated'] = compte.get('validated', False)  # Assurez-vous que le champ validé est défini
            comptes.append(compte)
        # Si les comptes sont récupérés avec succès, on les passe au template
        return render(request, 'clients/dashboard.html', {
            'comptes': comptes,
            'nom_client': nom_client
        })

    else:
        try:
            error_msg = response.json().get('error', 'Erreur inconnue')
        except Exception as e:
            print("Erreur JSON :", e)
            error_msg = response.text
        messages.error(request, f"Échec de la récupération des comptes : {error_msg}")
        comptes = []


    # Exemple de données de comptes pour le client
    # comptes = [
    #     {'type': 'Compte courant', 'numero': 'XXXX-XXXX-XXXX', 'solde': 1250.45},
    #     {'type': 'Livret A', 'numero': 'YYYY-YYYY-YYYY', 'solde': 3400.00},
    #     {'type': 'PEL', 'numero': 'ZZZZ-ZZZZ-ZZZZ', 'solde': 7800.50}
    # ]

        return render(request, 'clients/dashboard.html', {
            'comptes': comptes,
            'nom_client': nom_client
        })


def logout(request):
    # Supprime les cookies de session
    response = redirect('/auth/clients')
    response.delete_cookie('username')
    response.delete_cookie('password')
    response.delete_cookie('user')
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return response


def create_account(request):
    pass


def account_deposite(request):
    if request.method == "POST":
        compte_id = request.POST.get('compte')
        montant = request.POST.get('montant')
        username = request.COOKIES.get('username')
        password = request.COOKIES.get('password')

        if compte_id and montant:
            print("Tentative de dépôt sur le compte :", compte_id, "Montant :", montant)  # Pour debug
            response = requests.post(f"{DJANGO_HOST}/api/deposit", data={
                'compte_id': compte_id,
                'montant': montant,
                'username': username,
                'password': password
            })
            if response.ok:
                data = response.json()
                print("Dépôt réussi :", data)
                messages.success(request, f"Dépôt de {montant}€ sur le compte {compte_id} réussi.")
            else:
                try:
                    error_msg = response.json().get('error', 'Erreur inconnue')
                except Exception as e:
                    print("Erreur JSON :", e)
                    error_msg = response.text
                messages.error(request, f"Échec du dépôt : {error_msg}")
            return redirect('/clients/dashboard')  # Redirection après le dépôt
        else:
            messages.error(request, "Veuillez fournir un identifiant de compte et un montant.")
            return redirect('/clients/dashboard')
    else:
        messages.error(request, "Veuillez vous connecter d'abord.")
        return redirect('/auth/clients')