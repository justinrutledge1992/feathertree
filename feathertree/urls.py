from django.urls import path
from feathertree import views

urlpatterns = [
    path("", views.index, name="index")
]