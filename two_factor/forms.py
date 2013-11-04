from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from oath import accept_totp
from two_factor.models import TOKEN_METHODS
from django.conf import settings
import re

TF_FORWARD_DRIFT = getattr(settings,'TF_FORWARD_DRIFT', 1)
TF_BACKWARD_DRIFT = getattr(settings,'TF_BACKWARD_DRIFT', 1)

class ComputerVerificationForm(forms.Form):
    """
    Base class for computer verification. Extend this to get a form that
    accepts token values.
    """
    token = forms.CharField(label=_("Verification Code"), max_length=6,
                            widget=forms.TextInput(attrs={'autocomplete':'off'}))
    remember = forms.BooleanField(
        label=_("Remember this computer for 30 days"), required=False)

    error_messages = {
        'invalid_token': _("Please enter a valid code."),
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
    phone = forms.CharField(label=_('Phone Number'), max_length=14)
    
    def clean(self):
        phone = self.cleaned_data.get('phone', '')
        self.cleaned_data['phone'] = re.sub('[^+0-9]','', phone)
        return self.cleaned_data


class OptionalPhoneForm(PhoneForm):
    phone = forms.CharField(label=_('Phone Number'), max_length=14,
                            required=False)


class TokenVerificationForm(forms.Form):
    token = forms.CharField(label=_("Verification Code"), min_length=6, max_length=6,
                            widget=forms.TextInput(attrs={'autocomplete':'off'}))
    seed = None

    error_messages = {
        'invalid_token': _("Please enter a valid code."),
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
