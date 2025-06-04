from django.shortcuts import render
from django.http import HttpResponse


def auth_page(request):
    return render(request, 'banquier/auth.html')