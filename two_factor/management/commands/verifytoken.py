from __future__ import print_function
from django.contrib.auth.models import User
from django.core.management import BaseCommand, CommandError
from oath.totp import accept_totp
from django.conf import settings

TF_FORWARD_DRIFT = getattr(settings,'TF_FORWARD_DRIFT', 1)
TF_BACKWARD_DRIFT = getattr(settings,'TF_BACKWARD_DRIFT', 1)


class Command(BaseCommand):
    args = '<username token>'
    help = 'Verify a generated token'

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError('Please provide a username and password')
        try:
            user = User.objects.get(username=args[0])
        except User.DoesNotExist:
            raise CommandError('User with username "%s" not found' % args[0])

        if not user.tf_token:
            raise CommandError('User does not have a secret associated')

        accepted, drift = accept_totp(args[1], user.tf_token.seed,
                                      forward_drift=TF_FORWARD_DRIFT,
                                      backward_drift=TF_BACKWARD_DRIFT)

        if accepted:
            print("Token accepted (clock drifted {} seconds)".format(drift))
        else:
            print("Token not accepted")
