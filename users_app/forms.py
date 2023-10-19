from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    # add email address field to the form
    email = forms.EmailField(required=True)
    # first_name = forms.CharField(max_length=100, required=True)
    # last_name = forms.CharField(max_length=100, required=True)
    # add first name and last name fields to the form
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = User
        # specify the fields to display
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        