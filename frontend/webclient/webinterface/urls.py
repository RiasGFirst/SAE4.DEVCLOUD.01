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

    path('clients/deposit', clients.account_deposite, name='deposit_client'),
    path('client/withdraw', clients.account_withdraw, name='withdraw_client'),
    path('clients/create_account', clients.account_creation, name='create_account_client'),
    
    # Banquier URLs
    path('banquier/dashboard', banquier.manager_dashboard, name='dashboard_manager'),
    path('banquier/process_transaction', banquier.process_transaction, name='process_transaction'),


    path('banquier/logout', banquier.logout, name='logout_banquier'),

    # API URLs
    path('api/create_account', api.create_client, name='create_client'),
    path('api/connect_client', api.connect_client, name='connect_client'),
    path('api/get_accounts', api.get_accounts, name='get_accounts'),

    path('api/connect_banquier', api.connect_banquier, name='connect_banquier'),

    path('api/deposit', api.deposite_account, name='deposit_account'),
    path('api/withdraw', api.withdraw_account, name='withdraw_account'),
    path('api/account_creation', api.account_creation, name='create_account'),

    path('api/validate_transaction', api.process_transaction, name='process_transaction_api'),

    path('api/transactions', api.get_transactions, name='get_transactions'),
    path('api/accounts_pending', api.get_accounts_pending, name='get_accounts_pending'),
    

    # Add more URL patterns here as needed
]