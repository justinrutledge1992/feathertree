from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User, Story, Chapter
from django.utils import timezone


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

class StoryCreationForm(forms.ModelForm):
    # Extra (non-model) fields to bootstrap the first chapter
    first_chapter_title = forms.CharField(
        max_length=100,
        required=False,
        label=_("First Chapter Title"),
        help_text=_("Optional. You can leave this blank; chapters don’t have to be titled.")
    )
    first_chapter_content = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 10}),
        required=True,
        label=_("First Chapter Content"),
        help_text=_("Write the opening chapter of your story.")
    )

    class Meta:
        model = Story
        fields = ["title"]  # only exposed model field
        labels = {
            "title": _("Title"),
        }
        help_texts = {
            "title": _("Title your story! Note this title cannot change after you create it."),
        }

    # Override to create the Story (with given author) and also creates the first Chapter.
    def save(self, author=None, commit=True):
        if author is None:
            raise ValueError("StoryCreationForm.save(author=...) requires an author.")

        story = super().save(commit=False)
        story.author = author  # handled by view logic, passed in here
        if commit:
            story.save()

        chapter = Chapter(
            story=story,
            author=author,
            ordinal=1,
            title=self.cleaned_data.get("first_chapter_title", "") or "",
            content=self.cleaned_data["first_chapter_content"],
            draft=False,
        )
        if commit:
            chapter.save()

        return story, chapter

class ChapterCreationForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ["title", "content"]
        labels = {
            "title": _("Title"),
            "content": _("Content"),
        }
        help_texts = {
            "title": _("Title your chapter! Note this title cannot change after you create it. Chapter titles are not required."),
            "content": _("Write the text for your chapter here."),
        }