from django.shortcuts import render
from django.http import HttpResponse


def auth_page(request):
    return render(request, 'banquier/auth.html')

def manager_dashboard(request):
    # Liste simulée de transactions
    transactions = [
        {
            'id': 1,
            'type': 'Virement',
            'expediteur': 'Jean Dupont',
            'beneficiaire': 'Marie Durand',
            'montant': 250.00,
            'date': '2025-06-01'
        },
        {
            'id': 2,
            'type': 'Retrait',
            'expediteur': 'Sophie Martin',
            'beneficiaire': None,
            'montant': 100.00,
            'date': '2025-06-02'
        },
        {
            'id': 3,
            'type': 'Virement',
            'expediteur': 'Paul Morel',
            'beneficiaire': 'Lucie Leroy',
            'montant': 400.00,
            'date': '2025-06-03'
        }
    ]

    context = {
        'transactions': transactions,
        'nom_manager': 'Monsieur le Directeur'
    }

    return render(request, 'banquier/dashboard.html', context)