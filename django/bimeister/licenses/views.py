from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound


menu = [
    {'title': 'About site', 'url_name': 'about'},
    {'title': 'Licenses', 'url_name': 'licenses'},
    {'title': 'Feedback', 'url_name': 'feedback'},
    {'title': 'Contacts', 'url_name': 'contacts'},
    {'title': 'Login', 'url_name': 'login'}
]

data_db = [
    {'id': 1, 'title': 'Andy Hug', 'content': 'Biography of Andy Hug', 'is_published': True},
    {'id': 2, 'title': 'Mark Hunt', 'content': 'Biography of Mark Hunt', 'is_published': True},
    {'id': 3, 'title': 'Ramon Dekkers', 'content': 'Biography of Ramon Dekkers', 'is_published': True}
]

def index(request):
    data = {
        'title': 'Main page',
        'menu': menu,
        'posts': data_db,
    }
    return render(request, 'licenses/index.html', context=data)

def licenses(request, lic_id):
    return HttpResponse("<h2>Licenses page</h2>")

def show_post(requst, post_id):
    return HttpResponse(f"Post with id: {post_id}")

def about(request):
    return render(request, 'licenses/about.html')

def workflows(request):
    return HttpResponse("<h2>Workflows page</h2>")

def feedback(request):
    return HttpResponse("<h2>Feedback page</h2>")

def contacts(request):
    return HttpResponse("<h2>Contacts page</h2>")

def login(request):
    return HttpResponse("<h2>Login page</h2>")

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Page not found</h1>")