from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from .managers import UserManager
import datetime

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

# A Story is a set of chapters
class Story(models.Model):
    title = models.CharField(max_length=250) # Story titles are required
    def __str__(self):
        return self.title

# A Chapter is the basic building block of stories
class Chapter(models.Model):
    ordinal = models.IntegerField(default = 0) # This represents the sequence number from the beginning of the Story. 0 represents undedfined. First chapter should be "1"
    title = models.CharField(max_length=100, blank=True) # Chapter names are not required. Will save an empty string e.g. '' to the database.
    # The timestamp represents the date the chapter was written or draft last edited.
    timestamp = models.DateTimeField(auto_now=True) # Creates a timestamp every time the record is updated
    content = models.TextField() # requires some text
    draft = models.BooleanField(default=True)
    submitted_for_review = models.BooleanField(default=False) # used to track locked drafts
    # ForeignKey links Chapter to Story, establishing the one-to-many relationship
    # on_delete=models.CASCADE means if a Story is deleted, all their Chapters are also deleted.
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    previous_chapter = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="next_chapters",
        on_delete=models.CASCADE,  # or SET_NULL if you prefer
    )
    def __str__(self):
        return self.title