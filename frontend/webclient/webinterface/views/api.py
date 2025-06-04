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
    
"""
{
  "nom": "string",
  "email": "string",
  "mot_de_passe": "string",
  "role": "utiisateur"
}
"""
