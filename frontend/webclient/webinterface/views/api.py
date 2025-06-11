from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
import dotenv
import os

# Load environment variables from .env file
dotenv.load_dotenv()
API_HOST = os.getenv('API_HOST')

# Verify that API response is reachable
@csrf_exempt
def get_ping(request):
    response = requests.get(f"{API_HOST}/api/ping")
    if response.ok:
        data = response.json()
    return JsonResponse(data)

# Get the list of users
@csrf_exempt
def get_client(request):
    response = requests.get(f"{API_HOST}/api/user/")
    if response.ok:
        data = response.json()
    return JsonResponse(data)

@csrf_exempt
def create_client(request):
    if request.method == 'POST':
        data = {
            'nom': request.POST.get('username'),
            'email': request.POST.get('email'),
            'mot_de_passe': request.POST.get('password'),
            'role': 'utilisateur'
        }
        response = requests.post(f"{API_HOST}/api/user/", json=data)
        if response.ok:
            return JsonResponse(response.json(), status=201)
        else:
            return JsonResponse(response.json(), status=response.status_code)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def connect_client(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user with the API and use BASIC authentication
        response = requests.get(
            f"{API_HOST}/api/user/me",
            auth=(username, password),
            headers={'Content-Type': 'application/json'}
        )
        if response.ok:
            data = response.json()
            print(data)
            if data.get('role') != 'utilisateur':
                print("User is not a client.")
                return JsonResponse({"error": "User is not a client"}, status=403)
            print("Client authenticated successfully:", data)
            return JsonResponse(data)
        else:
            print("Authentication failed:", response.status_code, response.text)
            return JsonResponse({"error": "Authentication failed"}, status=response.status_code)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def get_accounts(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user with the API and use BASIC authentication
        response = requests.get(
            f"{API_HOST}/api/account/",
            auth=(username, password),
            headers={'Content-Type': 'application/json'}
        )
        if response.ok:
            data = response.json()
            print(data)
            if data == []:
                print("No accounts found for the user.")
                return JsonResponse({"error": "No accounts found"}, status=404)
            
            # If accounts are found, return them
            print("Accounts retrieved successfully:", data)
            return JsonResponse(data, safe=False)
        else:
            print("Authentication failed:", response.status_code, response.text)
            return JsonResponse({"error": "Authentication failed"}, status=response.status_code)
        

@csrf_exempt
def connect_banquier(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user with the API and use BASIC authentication
        response = requests.get(
            f"{API_HOST}/api/user/me",
            auth=(username, password),
            headers={'Content-Type': 'application/json'}
        )
        if response.ok:
            data = response.json()
            if data.get('role') != 'agent_bancaire':
                print("User is not a banquier.")
                return JsonResponse({"error": "User is not a banquier"}, status=403)
            print("Banquier authenticated successfully:", data)
            return JsonResponse(data)
        else:
            print("Authentication failed:", response.status_code, response.text)
            return JsonResponse({"error": "Authentication failed"}, status=response.status_code)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


def create_baccount(request):
    """
    Create a new bank account for a user.
    
    Expected JSON body:
    """
    pass


@csrf_exempt
def deposite_account(request):
    """
    Deposit money into a bank account.
    """
    if request.method == 'POST':
        compte_id = request.POST.get('compte_id')
        username = request.POST.get('username')
        password = request.POST.get('password')

        data = {
            'montant': request.POST.get('montant'),
        }
        response = requests.post(
            f"{API_HOST}/api/transaction/{compte_id}/depot",
            json=data,
            auth=(username, password),
            headers={'Content-Type': 'application/json'}
        )

        if response.ok:
            data = response.json()
            return JsonResponse(data, status=201)
        else:
            print("Deposit failed:", response.status_code, response.text)
            return JsonResponse(response.json(), status=response.status_code)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def get_transactions(request):
    if request.method == 'POST':
        username = request.POST.get('busername')
        password = request.POST.get('bpassword')

        if not username or not password:
            print("Username or password not provided.")
            return JsonResponse({"error": "Username or password not provided"}, status=400)
        response = requests.get(f"{API_HOST}/api/transaction/tovalidate",
                                auth=(username, password),
                                headers={'Content-Type': 'application/json'})
        print(response)
        if response.ok:
            data = response.json()
            if not data:
                print("No transactions to validate.")
                return JsonResponse({"error": "No transactions to validate"}, status=200)
            print("Transactions retrieved successfully:", data)
            return JsonResponse(data, safe=False)
        else:
            print("Failed to retrieve transactions:", response.status_code, response.text)
            return JsonResponse({"error": "Failed to retrieve transactions"}, status=response.status_code)


@csrf_exempt
def withdraw_account(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        compte_id = request.POST.get('compte_id')
        montant = request.POST.get('montant')

        if not compte_id or not montant:
            print("Account ID or amount not provided.")
            return JsonResponse({"error": "Account ID or amount not provided"}, status=400)
        
        if not username or not password:
            print("Username or password not provided.")
            return JsonResponse({"error": "Username or password not provided"}, status=400)

        data = {
            'montant': montant,
        }

        response = requests.post(f"{API_HOST}/api/transaction/{compte_id}/retrait",
                                json=data,
                                auth=(username, password),
                                headers={'Content-Type': 'application/json'})
        
        if response.ok:
            data = response.json()
            print("Withdraw request successful:", data)
            return JsonResponse(data, status=201)
        else:
            print("Withdraw request failed:", response.status_code, response.text)
            return JsonResponse(response.json(), status=response.status_code)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    

@csrf_exempt
def process_transaction(request):
    if request.method == 'POST':
        print(request.POST)
        transaction_id = request.POST.get('transaction_id')
        action = request.POST.get('action')
        username = request.POST.get('busername')
        password = request.POST.get('bpassword')

        if not transaction_id or not action:
            print("Transaction ID or action not provided.")
            return JsonResponse({"error": "Transaction ID or action not provided"}, status=400)
        if not username or not password:
            print("Username or password not provided.")
            return JsonResponse({"error": "Username or password not provided"}, status=400)
        
        if action not in ['validate', 'refuse']:
            print("Invalid action provided.")
            return JsonResponse({"error": "Invalid action provided"}, status=400)
        
        data = {
            "authorize": action == 'validate'
        }

        response = requests.post(f"{API_HOST}/api/transaction/validate/{transaction_id}",
                                 json=data,
                                auth=(username, password),
                                headers={'Content-Type': 'application/json'})
        
        if response.ok:
            data = response.json()
            print("Transaction processed successfully:", data)
            if action == 'validate':
                print(f"Transaction {transaction_id} validated successfully.")
            else:
                print(f"Transaction {transaction_id} refused successfully.")
            return JsonResponse(data, status=200)
        else:
            print("Transaction processing failed:", response.status_code, response.text)
            return JsonResponse(response.json(), status=response.status_code)
    else:
        print("Method not allowed for processing transaction.")
        return JsonResponse({"error": "Method not allowed"}, status=405)
    

@csrf_exempt
def account_creation(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        type_compte = request.POST.get('compte_type')

        if not username or not password or not type_compte:
            print("Username, password, or account type not provided.")
            return JsonResponse({"error": "Username, password, or account type not provided"}, status=400)
        
        #type_compte = courrant, livret et type: 'compte_courant', 'livret'
        if type_compte == 'courant':
            type = 'compte_courant'
        elif type_compte == 'livret':
            type = 'livret'
        else:
            print("Invalid account type provided.")
            return JsonResponse({"error": "Invalid account type provided"}, status=400)
        
        data = {
            'type': type,
            'solde_initial': 0
        }

        response = requests.post(f"{API_HOST}/api/account",
                                 json=data,
                                 auth=(username, password),
                                 headers={'Content-Type': 'application/json'})
        
        if response.ok:
            data = response.json()
            print("Account created successfully:", data)
            return JsonResponse(data, status=201)
        else:
            print("Account creation failed:", response.status_code, response.text)
            return JsonResponse(response.json(), status=response.status_code)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def get_accounts_pending(request):
    if request.method == 'POST':
        username = request.POST.get('busername')
        password = request.POST.get('bpassword')

        if not username or not password:
            print("Username or password not provided.")
            return JsonResponse({"error": "Username or password not provided"}, status=400)
        
        print("Fetching pending accounts for the dashboard:", username)
        
        response = requests.get(f"{API_HOST}/api/account/tovalidate",
                                auth=(username, password),
                                headers={'Content-Type': 'application/json'})
        
        if response.ok:
            data = response.json()
            if not data:
                print("No pending accounts found.")
                return JsonResponse({"error": "No pending accounts found"}, status=404)
            print("Pending accounts retrieved successfully:", data)
            return JsonResponse(data, safe=False)
        else:
            print("Failed to retrieve pending accounts:", response.status_code, response.text)
            return JsonResponse({"error": "Failed to retrieve pending accounts"}, status=response.status_code)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)