'''
Relevant takeaway from Django Docs:

- Mail is sent using the SMTP host and port specified in the EMAIL_HOST and EMAIL_PORT settings.
    The EMAIL_HOST_USER and EMAIL_HOST_PASSWORD settings, if set, are used to authenticate to the SMTP server,
    and the EMAIL_USE_TLS and EMAIL_USE_SSL settings control whether a secure connection is used.
    The character set of email sent with django.core.mail will be set to the value of your DEFAULT_CHARSET setting.

- Use these functions in all custom mailers:
    from django.core.mail:
    send_mail()
    send_mass_mail()
    mail_admins()
    mail_managers()

- The Django email functions outlined above all protect against header injection by forbidding newlines in header values.
    If any subject, from_email or recipient_list contains a newline (in either Unix, Windows or Mac style), 
    the email function (e.g. send_mail()) will raise django.core.mail.BadHeaderError (a subclass of ValueError) and, 
    hence, will not send the email. It’s your responsibility to validate all data before passing it to the email functions.

EXAMPLE: 
    send_mail(
        "Subject here",
        "Here is the message.",
        "from@example.com",
        ["to@example.com"],
        fail_silently=False,
    )

- The main difference between send_mass_mail() and send_mail() is that send_mail() opens a connection to the mail server each time it’s 
    executed, while send_mass_mail() uses a single connection for all of its messages. This makes send_mass_mail() slightly more efficient.
    
- mail_admins() prefixes the subject with the value of the EMAIL_SUBJECT_PREFIX setting, which is "[Django] " by default.
    The “From:” header of the email will be the value of the SERVER_EMAIL setting.

- django.core.mail.mail_managers() is just like mail_admins(), except it sends an email to the site managers, as defined in the MANAGERS setting.

'''

from django.core.mail import send_mail
from django.conf import settings
from .helpers import generate_new_user_activation_url

def send_new_user_confirmation_email(new_user):
    # generate unique url to confirmation page
    activation_url = generate_new_user_activation_url(new_user)

    # population send_mail arguments
    email_subject = "Feathertree - New Account Confirmation"
    email_body = "Welcome to Feathertree! Please click this link to activate your account: " + activation_url
    sender_address = settings.EMAIL_HOST_USER

    # send the email and return
    send_mail(email_subject, email_body, sender_address, [new_user.email], fail_silently=False,)
    return