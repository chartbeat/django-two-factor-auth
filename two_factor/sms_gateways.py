from datetime import datetime, timedelta
from django.conf import settings
from importlib import import_module
from django.utils.translation import ugettext

GATEWAY = getattr(settings, 'TF_SMS_GATEWAY', 'two_factor.sms_gateways.Fake')
RATE_LIMIT = getattr(settings, 'TF_RATE_LIMIT', 20)


def load_gateway(path):
    module, attr = path.rsplit('.', 1)
    mod = import_module(module)
    cls = getattr(mod, attr)
    return cls()


def get_gateway():
    return GATEWAY and load_gateway(GATEWAY)


def send(to, code, user_token=None, **kwargs):
    # user_token must be passed for rate limiting, but isn't required
    # because not all messages have a user token associated with them
    # (ie, the initial enable form messages)
    if user_token:
        time_window = datetime.now() - timedelta(seconds=RATE_LIMIT)
        if user_token.last_sent and user_token.last_sent > time_window:
            return {'ok': False,
                    'error_msg': 'You can only resend your code once every %d seconds.' % RATE_LIMIT}
        user_token.last_sent = datetime.now()
        user_token.save()
    return get_gateway().send(to=to, code=code, **kwargs)


class Fake(object):
    def send(self, to, code, **kwargs):
        print 'Fake SMS to %s: "Your token is: %s"' % (to, code)
        return {'ok': True}


class Twilio(object):
    def __init__(self, account=None, token=None, caller_id=None):
        if not account:
            account = getattr(settings, 'TWILIO_ACCOUNT_SID')
        if not token:
            token = getattr(settings, 'TWILIO_AUTH_TOKEN')
        if not caller_id:
            self.caller_id = getattr(settings, 'TWILIO_SMS_CALLER_ID')

        from twilio.rest import TwilioRestClient
        self.client = TwilioRestClient(account, token)

    def send(self, to, code, **kwargs):
        body = ugettext('Your authentication token is %s' % code)
        self.client.sms.messages.create(to=to, from_=self.caller_id, body=body)
