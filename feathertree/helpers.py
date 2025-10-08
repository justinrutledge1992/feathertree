from django.shortcuts import render
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import account_activation_token

# Include any miscellanous helper functions here
def generate_new_user_activation_url(user):
    domain_name = "feathertree.net"
    base_url = "https://" + domain_name + "/user/activation/"
    url_safe_user_id = urlsafe_base64_encode(force_bytes(user.pk))
    activation_token = account_activation_token.make_token(user)
    unique_url = base_url + url_safe_user_id + "/" + activation_token
    return unique_url

def form_invalid_response(request, form, template):
    return render(
        request,
        template,
        {
            "error_message": "Invalid form submission. Please make sure all fields are filled out properly and try again.",
            "form": form
        },
    )

def form_invalid_response_w_msg(request, form, template, error_message):
    return render(
        request,
        template,
        {
            "error_message": error_message,
            "form": form
        },
    )

def chunk_list(lst, chunk_size):
    chunks = []
    for i in range(0, len(lst), chunk_size):
        chunk = lst[i:i + chunk_size]
        while len(chunk) < chunk_size:  # Fill the chunk up to chunk_size
            chunk.append(None)
        chunks.append(chunk)
    return chunks