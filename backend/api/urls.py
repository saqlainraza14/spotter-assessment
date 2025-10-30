# backend/api/urls.py

from django.urls import path
from .views import TripCalculatorView

urlpatterns = [
    path('calculate-trip/', TripCalculatorView.as_view(), name='calculate-trip'),
]