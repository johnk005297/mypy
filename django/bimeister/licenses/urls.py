from django.urls import path, register_converter
from . import views
from . import converters



urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('licenses/<int:lic_id>/', views.licenses, name='licenses'),
    path('feedback/', views.feedback, name='feedback'),
    path('contacts/', views.contacts, name='contacts'),
    path('login/', views.login, name='login'),
    path('post/<int:post_id>/', views.show_post, name='post'),
]