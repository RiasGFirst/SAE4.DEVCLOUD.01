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
            return JsonResponse(data)
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



    
"""
{
  "nom": "string",
  "email": "string",
  "mot_de_passe": "string",
  "role": "utiisateur"
}
"""
