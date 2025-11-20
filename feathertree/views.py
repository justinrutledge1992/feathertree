from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.urls import reverse
from django.core.paginator import Paginator
from .models import User, Story, Chapter
from .forms import UserCreationForm, StoryCreationForm, ChapterCreationForm
from .helpers import form_invalid_response, form_invalid_response_w_msg
from .mailers import send_new_user_confirmation_email
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .tasks import review_chapter
import os

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
            new_user.is_active = True # CHANGE THIS TO FALSE WHEN A MAIL SERVER IS LIVE
            new_user.save()
            send_new_user_confirmation_email(new_user) # this is only meaningful if an email host exists
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
    
def story_view(request, story_id):
    story = get_object_or_404(Story, pk=story_id)
    chapters = (
        Chapter.objects
        .filter(story=story)
        .order_by("ordinal", "timestamp")
    )
    
    return render(request,"feathertree/story_view.html",{"story": story,"chapters": chapters})

def stories(request): # a list of recently updated stories
    stories_qs = (
        Story.objects
        .order_by("-last_updated")
    )

    paginator = Paginator(stories_qs, 10)  # 10 stories per page, make user-adjustable later
    page_number = request.GET.get("page")
    stories_page = paginator.get_page(page_number)

    print(stories_page)
    
    return render(request, "feathertree/stories.html", {
        "stories_page": stories_page,
    })


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
            story.last_updated = new_chapter.timestamp
            story.save()
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
    can_moderate = user.is_authenticated and user.is_staff

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
            return HttpResponseForbidden("Editing disabled.")
        form = ChapterCreationForm(request.POST, instance=chapter)
        if form.is_valid():
            obj = form.save(commit=False)
            # Save edits AND request publication in one go
            obj.submitted_for_review = True
            obj.save()
            # Create publication review task
            review_chapter.delay(chapter_id=chapter.id)
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
            "can_request_publish": can_request_publish,
            "can_publish": can_publish,
            "form": form,
        },
    )

# Static pages:
def new_user_instructions(request):
    return render(request, "feathertree/new_user_instructions.html")

def successful_logout(request):
    return render(request, "feathertree/index.html")

def successful_email_sent(request):
    return render(request, "feathertree/successful_email_sent.html")



##############################################################################################################################
# This page is only for test purposes, and will only change during brief production commits (this is dirty, I know, but quick)
'''
#from flow_judge.flow_judge import FlowJudge
#from flow_judge.models.huggingface import Hf
#from flow_judge.metrics.metric import CustomMetric, RubricItem
#from flow_judge.eval_data_types import EvalInput
def test_page(request):
    model = Hf(flash_attn=False)
    continuity_metric = CustomMetric(
        name="Story Continuity",
        criteria="Evaluate how well the current text continues a story from the previous text. Refer to the output as current text and the input as previous text. Do not refer to an input or output.",
        rubric=[
            RubricItem(score=1, description="No continuity. Very different in theme, tone, and content. New elements do not make sense in the context of the story."),
            RubricItem(score=2, description="Poor continuity. Somewhat different in theme, tone, and content. New elements do not make sense in the context of the story."),
            RubricItem(score=3, description="Some continuity. Somewhat aligned and also somewhat different in theme, tone, and content. New elements make sense in the context of the story."),
            RubricItem(score=4, description="Good continuity. Aligned in theme, tone, and content. New elements make sense in the context of the story."),
            RubricItem(score=5, description="Excellent continuity. Very aligned in theme, tone, and content. New elements make sense in the context of the story."),
        ],
        required_inputs=["previous_text"],
        required_output="current_text"
    )

    judge = FlowJudge(
        metric=continuity_metric,
        model=model
    )

    previous_text = """A man named Bob walked onto the street."""
    current_text = """Bob continued to walk down the street and avoid oncoming traffic."""

    eval_input = EvalInput(
    inputs=[
        {"previous_text": previous_text}
    ],
    output={"current_text": current_text},
    )

    result = judge.evaluate(eval_input, save_results=False)

    return render(request, "feathertree/test_page.html", {"feedback": result.feedback, "score": result.score})
'''

def test_page(request, chapter_id):
    # Get chapter by ID
    try:
        chapter = Chapter.objects.get(pk=chapter_id)
    except Chapter.DoesNotExist:
        return 0, f"Chapter with ID {chapter_id} not found."
    
    content = chapter.content
    score = 0
    feedback = ""

    # Start with this chapter’s content
    previous_text = ""

    # Walk backward through linked chapters
    current = chapter
    while current.previous_chapter is not None:
        current = current.previous_chapter
        previous_text = current.content + "\n" + previous_text  # prepend previous content

    return render(request, "feathertree/test_page.html", {"content": content, "previous_text": previous_text})