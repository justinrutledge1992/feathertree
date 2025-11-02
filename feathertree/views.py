from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.urls import reverse
from .models import User, Story, Chapter
from .forms import UserCreationForm, StoryCreationForm, ChapterCreationForm
from .helpers import form_invalid_response, form_invalid_response_w_msg
from .mailers import send_new_user_confirmation_email
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib import messages
import re

def index(request):
    return render(request, "feathertree/index.html")

# User Views
def user_create(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        # Create, but don't save the new user instance.
        form = UserCreationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            new_user = form.save(commit=False)
            new_user.is_active = False
            new_user.save()
            send_new_user_confirmation_email(new_user)
            # redirect to a static page and tell users to check their email:
            return HttpResponseRedirect(reverse("feathertree:new_user_instructions"))
        else:
            return form_invalid_response(request, form, "feathertree/user_create.html")
    else: # prcoess GET request
        form = UserCreationForm()
        return render(request, "feathertree/user_create.html", {"form": form})
    
def user_profile(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)

    # Fetch all chapters written by this user, along with their stories
    chapters = (
        Chapter.objects
        .filter(author=profile_user)
        .select_related("story")
        .order_by("story__title", "ordinal")
    )

    return render(request,"feathertree/user_profile.html",{"profile_user": profile_user,"chapters": chapters})

def user_deactivate(request, user_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("feathertree:index"))
    else: # user is logged in
    # PROCESS POST REQUEST & FORM HERE
    # you can pull the user directly from the template if authenticated
        if request.user.pk == user_id: # allow the form IF AND ONLY IF the user to be deactivated is the same as the logged in user
            user_to_deactivate = get_object_or_404(User, pk=user_id)
            context = {"user_to_deactivate": user_to_deactivate}
            return render(request, "feathertree/user_deactivate.html", context)
        else:
            return HttpResponseRedirect(reverse("feathertree:index",))

def user_activation(request, **kwargs):
    # parse URL arguments
    user_id = force_str(urlsafe_base64_decode(kwargs["uidb64"]))
    activation_token = kwargs["token"]
    user_to_activate = get_object_or_404(User, pk=user_id)
    if user_to_activate.is_active: # Ignore completely if user is already active
        return HttpResponseRedirect(reverse("feathertree:index",))
    else:
        if account_activation_token.check_token(user_to_activate, activation_token):
            user_to_activate.is_active = True
            user_to_activate.save()
            login(request, user_to_activate)
            return render(request, "feathertree/user_activation.html")
        else:
            return HttpResponseRedirect(reverse("feathertree:index"))

# Story Views:
def story_create(request):
    if request.method == "POST":
        form = StoryCreationForm(request.POST)
        if form.is_valid():
            story, chapter = form.save(author=request.user, commit=True)
            return redirect("feathertree:chapter_view", chapter_id=chapter.id)
        return render(request, "feathertree/story_create.html", {"form": form})
    else:
        form = StoryCreationForm()
        return render(request, "feathertree/story_create.html", {"form": form})

# Used to create a chapter beyond the first one
def chapter_create(request, prev_chapter_id):
    prev_chapter = get_object_or_404(Chapter, pk=prev_chapter_id)
    story = prev_chapter.story
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        form = ChapterCreationForm(request.POST)
        if form.is_valid():
            new_chapter = form.save(commit=False)
            new_chapter.story = story
            new_chapter.author = request.user
            new_chapter.ordinal = (prev_chapter.ordinal) + 1
            new_chapter.previous_chapter = prev_chapter  # point this new chapter to the previous chapter in the database
            new_chapter.save()
            return redirect("feathertree:chapter_view", chapter_id=new_chapter.id)
        # fallback: render with errors
        else:
            return render(request, "feathertree/chapter_create.html", {"form": form,"story": story,"prev_chapter": prev_chapter})
    else: # process GET request
        form = ChapterCreationForm()
        return render(request, "feathertree/chapter_create.html", {"form": form, "prev_chapter_id": prev_chapter_id})
    
# The Story view simply find the first chapter in the story and redirects the user there
def story_view(request, story_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("feathertree:index"))
    else:
        story = get_object_or_404(Story, pk=story_id)
        first_chapter = story.chapters.filter(ordinal=1).first()
        return redirect("feathertree:chapter_view", chapter_id=first_chapter.id)

def chapter_view(request, chapter_id):
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    user = request.user

    is_author = user.is_authenticated and (user == getattr(chapter, "author", None))
    can_moderate = user.is_authenticated and (
        user.is_staff or user.has_perm("feathertree.change_chapter")  # adjust app label if needed
    )

    # View permission (don’t tie to can_edit)
    can_view_draft = (not chapter.draft) or is_author or can_moderate
    if not can_view_draft:
        raise Http404("Chapter not found")

    # Capabilities
    can_edit = (is_author or can_moderate) and chapter.draft and (not chapter.submitted_for_review)
    # You can keep these for template state if you still show anything else:
    can_request_publish = is_author and chapter.draft and (not chapter.submitted_for_review)
    can_publish = can_moderate and chapter.draft

    # Default form
    form = ChapterCreationForm(instance=chapter) if can_edit else None

    if request.method == "POST":
        if not can_edit:
            return HttpResponseForbidden("Editing disabled while awaiting review or you lack permission.")
        form = ChapterCreationForm(request.POST, instance=chapter)
        if form.is_valid():
            obj = form.save(commit=False)
            # Save edits AND request publication in one go
            obj.submitted_for_review = True
            obj.save()
            return redirect("feathertree:chapter_view", chapter_id=chapter.id)
        # if invalid, fall through and render with errors

    next_chapters = (
        chapter.next_chapters.all().select_related("story").order_by("timestamp")
    )
    if not (is_author or can_moderate):
        next_chapters = next_chapters.filter(draft=False)

    return render(
        request,
        "feathertree/chapter_view.html",
        {
            "chapter": chapter,
            "previous_chapter": chapter.previous_chapter,
            "next_chapters": next_chapters,
            "can_edit": can_edit,
            "can_request_publish": can_request_publish,  # optional now
            "can_publish": can_publish,                  # optional
            "form": form,
        },
    )

def chapter_publish(request, chapter_id):
    chapter = get_object_or_404(Chapter, pk=chapter_id)

    if not request.user.is_authenticated or request.user != chapter.author:
        return redirect("feathertree:chapter_view", chapter_id=chapter.id)

    # Example logic: mark for moderation
    chapter.submitted_for_review = True
    chapter.save()
    messages.success(request, "Your publication request has been sent for review.")
    return redirect("feathertree:chapter_view", chapter_id=chapter.id)

# Static pages:
def new_user_instructions(request):
    return render(request, "feathertree/new_user_instructions.html")

def successful_logout(request):
    return render(request, "feathertree/index.html")

def successful_email_sent(request):
    return render(request, "feathertree/successful_email_sent.html")

# This page is only for test purposes, and will only change during brief production commits (this is dirty, I know, but quick)
from feathertree_project.celery import divide
def test_page(request):
    task = divide.delay(1, 2)
    # Block this request thread up to 10s waiting for the result
    result = task.get(timeout=10)  # raises TimeoutError if it takes too long
    ctx = {
        "status": task.status,   # likely "SUCCESS"
        "result": result,        # 0.5
        "task_id": task.id,
    }
    return render(request, "feathertree/test_page.html", ctx)