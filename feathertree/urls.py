from django.urls import path
from feathertree import views

urlpatterns = [
    path("", views.home, name="home")
]