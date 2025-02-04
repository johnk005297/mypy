from django.shortcuts import render
from django.http import HttpResponse

def licenses(request): # HttpRequest
    return HttpResponse("Licenses web page")

def workflows(request):
    return HttpResponse("<h1> Workflows </h1>")