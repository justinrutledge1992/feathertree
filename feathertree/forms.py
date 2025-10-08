from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User

# User Forms
class UserCreationForm(DjangoUserCreationForm):
    display_name = forms.CharField(
        max_length=40,
        required=True,
        label=_("Username"),
        help_text=_("This will be your public display name."),
    )

    email = forms.EmailField(
        required=True,
        label=_("Email address"),
        help_text=_("You'll use this email to log in."),
    )

    class Meta:
        model = User
        fields = ["display_name", "email", "password1", "password2"]