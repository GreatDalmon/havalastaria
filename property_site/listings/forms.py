from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Property, Agent

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        # We include all fields EXCEPT 'agent' and 'created_at'.
        # We will set the 'agent' automatically based on who is logged in!
        fields = ['title', 'description', 'location', 'price', 'property_type',
                    'bedrooms', 'bathrooms', 'square_feet', 'year_built', 'image']


class AgentCreateForm(forms.Form):
    """Staff-only: creates a login account and its Agent profile in one step."""
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    phone_number = forms.CharField(max_length=20)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)

    def clean_username(self):
        name = self.cleaned_data['username']
        if User.objects.filter(username__iexact=name).exists():
            raise ValidationError('That username is already taken.')
        return name

    def clean(self):
        data = super().clean()
        pw = data.get('password')
        if pw:
            try:
                validate_password(pw, user=User(username=data.get('username', ''),
                                                first_name=data.get('first_name', ''),
                                                last_name=data.get('last_name', '')))
            except ValidationError as e:
                self.add_error('password', e)
        return data

    @transaction.atomic
    def save(self):
        d = self.cleaned_data
        user = User.objects.create_user(username=d['username'], password=d['password'],
                                        first_name=d['first_name'], last_name=d['last_name'])
        return Agent.objects.create(user=user, phone_number=d['phone_number'], bio=d['bio'])
