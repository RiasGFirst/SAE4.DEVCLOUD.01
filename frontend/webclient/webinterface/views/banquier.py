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
    response = requests.post(f"{DJANGO_HOST}/api/transactions", data={
        'busername': request.COOKIES.get('busername'),
        'bpassword': request.COOKIES.get('bpassword')
    })

    if response.ok:
        transactions_data = response.json()
        

        print("Transactions data:", transactions_data)

        # verification que la liste na pas le "error"
        if isinstance(transactions_data, dict) and 'error' in transactions_data:
            return render(request, 'banquier/dashboard.html', {'transactions': [], 'nom_manager': request.COOKIES.get('buser', 'Manager inconnu')})
        
        else:
        # [{'processed': False, 'compte_source_id': 1, 'type_operation': 'retrait', 'compte_destination_id': None, 'date_creation': '2025-06-10T12:58:35.139341+00:00', 'id': 3, 'montant': -0.69}]

            for transaction in transactions_data:
                transaction['date_creation'] = transaction['date_creation'].split('T')[0]
                transaction['montant'] = abs(transaction['montant'])  # Assure que le montant est positif
            transactions = [
                {
                    'id': transaction['id'],
                    'type': transaction['type_operation'].capitalize(),
                    'expediteur': transaction.get('compte_source_id') or 'Inconnu',
                    'beneficiaire': transaction.get('compte_destination_id') or 'Inconnu',
                    'montant': transaction['montant'],
                    'date': transaction['date_creation']
                } for transaction in transactions_data
            ]
            print("Processed transactions:", transactions)
            context = {
                'transactions': transactions,
                'nom_manager': request.COOKIES.get('buser', 'Manager inconnu'),
            }

            return render(request, 'banquier/dashboard.html', context)
    else:
        print("Failed to fetch transactions:", response.status_code, response.text)
        messages.error(request, "Échec de la récupération des transactions.")

    # transactions = [
    #     {
    #         'id': 1,
    #         'type': 'Virement',
    #         'expediteur': 'Jean Dupont',
    #         'beneficiaire': 'Marie Durand',
    #         'montant': 250.00,
    #         'date': '2025-06-01'
    #     },
    #     {
    #         'id': 2,
    #         'type': 'Retrait',
    #         'expediteur': 'Sophie Martin',
    #         'beneficiaire': None,
    #         'montant': 100.00,
    #         'date': '2025-06-02'
    #     },
    #     {
    #         'id': 3,
    #         'type': 'Virement',
    #         'expediteur': 'Paul Morel',
    #         'beneficiaire': 'Lucie Leroy',
    #         'montant': 400.00,
    #         'date': '2025-06-03'
    #     }
    # ]

    transactions = []

    context = {
        'transactions': transactions,
        'nom_manager': request.COOKIES.get('buser', 'Manager inconnu'),
    }

    return render(request, 'banquier/dashboard.html', context)


def process_transaction(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        action = request.POST.get('action')  # 'valider' or 'refuser'
        busername = request.COOKIES.get('busername')
        bpassword = request.COOKIES.get('bpassword')

        print("busername:", busername)
        print("bpassword:", bpassword)
        print("transaction_id:", transaction_id)
        print("action:", action)

        if transaction_id and action:
            print(f"Processing transaction {transaction_id} with action {action}")

            response = requests.post(f"{DJANGO_HOST}/api/validate_transaction",
                                    data={
                                        'transaction_id': transaction_id,
                                        'action': action,
                                        'busername': busername,
                                        'bpassword': bpassword
                                    })
            if response.ok:
                data = response.json()
                print("Transaction processed successfully:", data)
                if action == 'validate':
                    messages.success(request, f"Transaction {transaction_id} validée avec succès.")
                else:
                    messages.success(request, f"Transaction {transaction_id} refusée avec succès.")
            return redirect('dashboard_manager')
        else:
            messages.error(request, "Transaction ID ou action non fournis.")
            return redirect('dashboard_manager')
    else:
        messages.error(request, "Méthode non autorisée.")
        return redirect('dashboard_manager')




def logout(request):
    # Supprime les cookies de session
    response = redirect('auth_banquier_page')
    response.delete_cookie('busername')
    response.delete_cookie('bpassword')
    response.delete_cookie('buser')
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return response