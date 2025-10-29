from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from .models import User, Story, Chapter
from .forms import UserCreationForm, StoryCreationForm, ChapterCreationForm

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

class StoryAdmin(admin.ModelAdmin):
    add_form = StoryCreationForm
    model = Story
    list_display = ("title",)
    list_filter = ("title",)
    search_fields = ("title",)


class ChapterAdmin(admin.ModelAdmin):
    add_form = ChapterCreationForm
    model = Chapter
    list_display = ("title", "timestamp", "author", "story", "ordinal", "draft", "previous_chapter")
    list_filter = ("title", "timestamp", "author", "story", "ordinal", "draft", "previous_chapter")
    ordering = ("-timestamp",)
    search_fields = ("title", "author", "story")

# Register all models here.
admin.site.register(User, UserAdmin)
admin.site.register(Story, StoryAdmin)
admin.site.register(Chapter, ChapterAdmin)
