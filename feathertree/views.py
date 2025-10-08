from django.http import HttpResponse
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .models import User
from .forms import UserCreationForm
from .helpers import form_invalid_response, form_invalid_response_w_msg
from .mailers import send_new_user_confirmation_email
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
import re

def index(request):
    return render(request, "feathertree/index.html")

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
            email = new_user.email
            domain_and_extension = email.split("@")[1]
            if not (re.match(domain_and_extension, "benedictine.edu") or re.match(domain_and_extension, "ravens.benedictine.edu")):
                return form_invalid_response_w_msg(request, UserCreationForm(request.POST), "feathertree/user_create.html", "Sorry, but it looks like you don't even go here. Use your college email address to create your account so we can keep this site safe.")
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
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("feathertree:index"))
    else: # user is logged in
        profile_user = get_object_or_404(User, pk=user_id)
        user_cards = profile_user.cards.all().order_by("-publish_date") 
        context = {"profile_user": profile_user, "user_cards": user_cards} # represents the user whose profile is being viewed
        return render(request, "feathertree/user_profile.html", context)


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

# Static pages:
def new_user_instructions(request):
    return render(request, "feathertree/new_user_instructions.html")

def successful_logout(request):
    return render(request, "feathertree/index.html")

def successful_email_sent(request):
    return render(request, "feathertree/successful_email_sent.html")

# This page is only for test purposes, and will only change during brief production commits (this is dirty, I know, but quick)
def test_page(request):
    return render(request, "feathertree/index.html")