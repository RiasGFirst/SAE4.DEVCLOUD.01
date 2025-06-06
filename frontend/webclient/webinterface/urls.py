from django.urls import path, include
from .views import home, clients, banquier, api

urlpatterns = [
    # Home page
    path('', home.index, name='index'),

    # Authentifaction URLs
    path('auth/clients', clients.auth_page, name='auth_client_page'),
    path('auth/banquier', banquier.auth_page, name='auth_banquier_page'),

    # Client management URLs
    path('clients/dashboard', clients.dashboard_client, name='dashboard_client'),
    path('clients/logout', clients.logout, name='logout_client'),
    
    # Banquier URLs
    path('banquier/dashboard', banquier.manager_dashboard, name='dashboard_manager'),
    path('banquier/logout', banquier.logout, name='logout_banquier'),

    # API URLs
    path('api/create_account', api.create_client, name='create_client'),
    path('api/connect_client', api.connect_client, name='connect_client'),
    path('api/get_accounts', api.get_accounts, name='get_accounts'),

    path('api/connect_banquier', api.connect_banquier, name='connect_banquier'),
    

    # Add more URL patterns here as needed
]