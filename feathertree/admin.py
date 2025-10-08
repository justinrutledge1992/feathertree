from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from .models import User
from .forms import UserCreationForm

# Override admin site attributes:
    # Text to put at the end of each page's <title>.
admin.site.site_title = 'Feathertree Site Admin'
    # Text to put in each page's <h1> (and above login form).
admin.site.site_header = 'Feathertree Administration'
    # Text to put at the top of the admin index page.
admin.site.index_title = 'Feathertree Administration'

# Create admin logic for all models here
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    model = User
    list_display = ("display_name", "email", "is_staff", "is_active", "date_joined")
    list_filter = ("display_name", "email", "is_staff", "is_active", "date_joined")
    fieldsets = (
        (None, {"fields": ("display_name", "email", "password",)}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_restricted", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "display_name", "email", "password1", "password2", "is_staff",
                "is_active", "is_restricted", "groups", "user_permissions"
            )}
        ),
    )
    search_fields = ("display_name", "email",)
    ordering = ("-date_joined",)

# Register all models here.
admin.site.register(User, UserAdmin)