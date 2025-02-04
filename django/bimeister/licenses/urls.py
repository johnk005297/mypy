from django.urls import path
from . import views

urlpatterns = [
    path('licenses/', views.licenses),
    path('workflows/', views.workflows),
]