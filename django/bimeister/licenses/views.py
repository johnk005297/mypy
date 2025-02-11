from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound

def licenses(request, lic_id): # HttpRequest
    return HttpResponse(f"<h2>Licenses web page</h2><p>this is int id: {lic_id}</p>")

def licenses_by_slug(request, lic_slug):
    return HttpResponse(f"<h2>Licenses web page</h2><p>this is slug id: {lic_slug}</p>")

def workflows(request):
    return HttpResponse("<h1> Workflows </h1>")

def archive(request, year):
    return HttpResponse(f"<h1>Welcome to archive</h1><p>this is year id: {year}</p>")

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Page not found</h1>")