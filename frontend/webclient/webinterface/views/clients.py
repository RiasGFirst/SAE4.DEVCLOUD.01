from django.shortcuts import render, redirect
from django.contrib import messages  # 👈 important
from django.http import HttpResponse


def auth_page(request):
    if request.method == "POST":
        if "register" in request.POST:
            username = request.POST.get("username")
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")

            if password1 == password2:
                # Ici tu peux appeler une API pour l’enregistrement ou créer l’utilisateur
                messages.success(request, f"L'utilisateur {username} a été inscrit avec succès.")
                return redirect('/auth/clients')  # 👈 redirection après succès pour éviter double POST
            else:
                messages.error(request, "Les mots de passe ne correspondent pas. Réessaie.")
                return redirect('/auth/clients')

        elif "login" in request.POST:
            username = request.POST.get("username")
            password = request.POST.get("password")

            # Authentifie avec une API ou ton système
            if username and password:  # Simule une réussite
                messages.success(request, f"Bienvenue {username} ! Connexion réussie.")
                return redirect('/auth/clients')
            else:
                messages.error(request, "Identifiants invalides. Merci de réessayer.")
                return redirect('/auth/clients')

    return render(request, 'clients/auth.html')
