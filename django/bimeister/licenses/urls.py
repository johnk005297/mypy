from django.urls import path, register_converter
from . import views
from . import converters

register_converter(converters.FourDigitYearConverter, "yyyy")

urlpatterns = [
    path('workflows/', views.workflows),
    path('licenses/<int:lic_id>/', views.licenses),
    path('licenses/<slug:lic_slug>/', views.licenses_by_slug),
    path('archive/<yyyy:year>/', views.archive)
]