from django.contrib.auth.backends import ModelBackend
from django.utils.timezone import now
from oath import accept_totp
from django.conf import settings

TF_FORWARD_DRIFT = getattr(settings,'TF_FORWARD_DRIFT', 1)
TF_BACKWARD_DRIFT = getattr(settings,'TF_BACKWARD_DRIFT', 1)


class TokenBackend(ModelBackend):
    def authenticate(self, request, user, token):
        accepted, drift = accept_totp(key=user.tf_token.seed, response=token,
                                      forward_drift=TF_FORWARD_DRIFT,
                                      backward_drift=TF_BACKWARD_DRIFT)
        return user if accepted else None


class VerifiedComputerBackend(ModelBackend):
    def authenticate(self, request, user, computer_id):
        verification = user.tf_verified_computers.get(pk=computer_id)
        if verification.verified_until < now():
            return None
        verification.last_used_at = now()
        verification.save()
        return user
