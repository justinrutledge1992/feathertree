from django.contrib.auth.tokens import PasswordResetTokenGenerator

#Extend PasswordResetTokenGenerator for new account activation
class ActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.username) + str(user.pk) + str(timestamp)
        )
account_activation_token = ActivationTokenGenerator()