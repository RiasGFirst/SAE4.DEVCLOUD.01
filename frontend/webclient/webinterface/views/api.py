from django.http import JsonResponse
import requests
import dotenv
import os

# Load environment variables from .env file
dotenv.load_dotenv()
API_HOST = os.getenv('API_HOST')

# Verify that API response is reachable
def get_ping(request):
    response = requests.get(f"{API_HOST}/api/ping")
    if response.ok:
        data = response.json()
    return JsonResponse(data)

# Get the list of clients
def get_client(request):
    response = requests.get(f"{API_HOST}/api/user/me")
    if response.ok:
        data = response.json()
    return JsonResponse(data)

# Get the list of accounts for a client


