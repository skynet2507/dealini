from django.http import HttpResponse
from django.shortcuts import render


def home_page(request):
    return render(request, "home.html")


def urls_page(request):
    return render(request, "urls.html")
