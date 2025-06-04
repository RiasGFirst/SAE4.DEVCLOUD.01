from django.urls import path, include
from .views import home, clients, banquier

urlpatterns = [
    # Home page
    path('', home.index, name='index'),

    # Authentifaction URLs
    path('auth/clients', clients.auth_page, name='auth_client_page'),
    path('auth/banquier', banquier.auth_page, name='auth_banquier_page'),

    # Client management URLs
    
    # Banquier URLs

    # API URLs
    

    # Add more URL patterns here as needed
]