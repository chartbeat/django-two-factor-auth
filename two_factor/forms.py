from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from oath import accept_totp
from two_factor.models import TOKEN_METHODS
from django.conf import settings

TF_FORWARD_DRIFT = getattr(settings,'TF_FORWARD_DRIFT', 1)
TF_BACKWARD_DRIFT = getattr(settings,'TF_BACKWARD_DRIFT', 1)

class ComputerVerificationForm(forms.Form):
    """
    Base class for computer verification. Extend this to get a form that
    accepts token values.
    """
    token = forms.CharField(label=_("Token"), max_length=6)
    remember = forms.BooleanField(
        label=_("Remember this computer for 30 days"), required=False)

    error_messages = {
        'invalid_token': _("Please enter a valid token."),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, request=None, user=None, **kwargs):
        self.user = user
        super(ComputerVerificationForm, self).__init__(**kwargs)

    def clean(self):
        token = self.cleaned_data.get('token')

        if token:
            self.user_cache = authenticate(token=token, user=self.user)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_token'])
            elif not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'])
        return self.cleaned_data


class MethodForm(forms.Form):
    method = forms.ChoiceField(label=_("Method"), choices=TOKEN_METHODS,
                               widget=forms.RadioSelect)


class PhoneForm(forms.Form):
    error_messages = {
        'invalid_phone': _('Please enter a valid phone number, including your '
                           'country code starting with + or 00.')
    }

    phone = forms.RegexField('^(\+|00)', label=_('Phone Number'),
                             error_message=error_messages['invalid_phone'])


class TokenVerificationForm(forms.Form):
    token = forms.CharField(label=_("Token"), min_length=6, max_length=6)
    seed = None

    error_messages = {
        'invalid_token': _("Please enter a valid token."),
    }

    def clean(self):
        token = self.cleaned_data.get('token')
        if token:
            accepted, drift = accept_totp(key=self.seed, response=token,
                                          forward_drift=TF_FORWARD_DRIFT,
                                          backward_drift=TF_BACKWARD_DRIFT)
            if not accepted:
                raise forms.ValidationError(
                    self.error_messages['invalid_token'])
        return self.cleaned_data


class DisableForm(forms.Form):
    understand = forms.BooleanField(label=_("Yes, I am sure"))
