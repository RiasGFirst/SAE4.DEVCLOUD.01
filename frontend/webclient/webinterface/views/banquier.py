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

    buser = request.COOKIES.get('buser')
    busername = request.COOKIES.get('busername')
    bpassword = request.COOKIES.get('bpassword')
    transactions = []
    accounts_pending = []

    # Récupère les transactions en attente
    response1 = requests.post(f"{DJANGO_HOST}/api/transactions", data={
        'busername': busername,
        'bpassword': bpassword
    })

    # Liste des comptes en attente de validation
    response2 = requests.post(f"{DJANGO_HOST}/api/accounts_pending", data={
        'busername': busername,
        'bpassword': bpassword
    })

    if response1.ok and response2.ok:
        transactions_error = False
        accounts_pending_error = False
        transactions_data = response1.json()
        accounts_pending_data = response2.json()
        print("Transactions:", transactions_data)
        print("Accounts pending:", accounts_pending_data)

        # Si les données sont vides, on affiche un message
        if isinstance(transactions_data, dict) and 'error' in transactions_data:
            messages.info(request, "Aucune transaction en attente.")
            transactions_error = True
        if isinstance(accounts_pending_data, dict) and 'error' in accounts_pending_data:    
            messages.info(request, "Aucun compte en attente de validation.")
            accounts_pending_error = True

        print("Transactions:", transactions_data)
        print("Accounts pending:", accounts_pending_data)

        # Si error == True on n'affiche pas les transactions ou les comptes en attente
        if not transactions_error:
            for transaction in transactions_data:
                transaction['date_creation'] = transaction['date_creation'].split('T')[0]
                transaction['montant'] = abs(transaction['montant'])  # Assure que le montant est positif

            transactions = [
                {
                    'id': transaction['id'], #
                    'type': transaction['type_operation'].capitalize(),
                    'expediteur': transaction.get('_compte_source', {}).get('iban', 'Inconnu') or 'Inconnu', # IBAN de l'expéditeur
                    'beneficiaire': transaction.get('_compte_destination', {}).get('iban', 'Inconnu') or 'Inconnu' if transaction.get('_compte_destination') else None,  # IBAN du bénéficiaire
                    'montant': transaction['montant'],
                    'date': transaction['date_creation']
                } for transaction in transactions_data
            ]
        else:
            transactions = []
        if not accounts_pending_error:
            for account in accounts_pending_data:
                account['date_creation'] = account['date_creation'].split('T')[0]

            accounts_pending = [
                {
                    'id': account['id'],
                    'iban': account['iban'],
                    'type_compte': account['type_compte'].capitalize(),  # Met le type de compte en majuscule
                    'solde': float(account['solde']),
                    'date_creation': account['date_creation'].split('T')[0]  # Formate la date
                } for account in accounts_pending_data
            ]
        else:
            accounts_pending = []

        return render(request, 'banquier/dashboard.html', {
            'transactions': transactions,
            'accounts_pending': accounts_pending,
            'nom_manager': buser or 'Manager Inconnu'
        })

    else:
        print("Failed to fetch transactions or accounts pending.")
        messages.error(request, "Erreur lors de la récupération des données. Veuillez réessayer plus tard.")
        transactions = []
        accounts_pending = []

        return render(request, 'banquier/dashboard.html', {
            'transactions': transactions,
            'accounts_pending': accounts_pending,
            'nom_manager': busername or 'Manager Inconnu'
        })





def process_transaction(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        action = request.POST.get('action')  # 'valider' or 'refuser'
        busername = request.COOKIES.get('busername')
        bpassword = request.COOKIES.get('bpassword')

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
    

def process_account(request):
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        action = request.POST.get('action')  # 'valider' or 'refuser'
        busername = request.COOKIES.get('busername')
        bpassword = request.COOKIES.get('bpassword')
        if account_id and action:
            response = requests.post(f"{DJANGO_HOST}/api/validate_account",
                                    data={
                                        'account_id': account_id,
                                        'action': action,
                                        'busername': busername,
                                        'bpassword': bpassword
                                    })
            if response.ok:
                try:
                    data = response.json()
                except ValueError:
                    data = {}
                    print("No content returned, assuming success without data.")
                print("Account processed successfully:", data)
                if action == 'validate':
                    messages.success(request, f"Compte {account_id} validé avec succès.")
                else:
                    messages.success(request, f"Compte {account_id} refusé avec succès.")
            return redirect('dashboard_manager')
        else:
            messages.error(request, "Account ID ou action non fournis.")
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