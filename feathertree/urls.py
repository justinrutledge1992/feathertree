from django.contrib import admin
from django.urls import path, include
from . import views

app_name = "feathertree" # namespace for URLs when referenced dynamically in the views/templates

urlpatterns = [
    # Index URL:
    path("", views.index, name="index"),

    # User URLs:
    path("user/create", views.user_create, name="user_create"),
    #path("user/update", views.user_update, name="user_update"),
    path("user/<int:user_id>/profile", views.user_profile, name="user_profile"),
    path("user/activation/<uidb64>/<token>/", views.user_activation, name="user_activation"),

    # Static Page URLs:
    path("user/new-user-instructions", views.new_user_instructions, name="new_user_instructions"),
    path("user/successful-logout", views.successful_logout, name="successful_logout"),

    # Test Page (intended for rapid testing of new backend functionality):
    path("test-page", views.test_page, name="test_page"),
]