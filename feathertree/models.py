from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from .managers import UserManager

# Field Classes
# These are all Django class extensions & Django method overrides
class LowerCaseCharField(models.CharField):
    def get_prep_value(self, value):
        return str(value).lower()

# Models
class User(AbstractUser):
    # Disable the built-in username for auth
    username = None

    # Keep email as unique login field
    email = models.EmailField("email address", unique=True)

    # Add a separate username field for display/profile
    display_name = models.CharField("username", max_length=40, unique=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    is_restricted = models.BooleanField(default=False)  # For view-only privileges

    objects = UserManager()

    def email_prefix_tag(self):
        return "@" + self.email.split("@")[0]

    def __str__(self):
        return self.email

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("email"),
                name="user_email_case_insensitive_uniqueness",
                violation_error_message="The email address you entered has already been used to sign up for an account.",
            ),
        ]
