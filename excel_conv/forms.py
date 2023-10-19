from django import forms
from .models import ConvJob


class UploadJobForm(forms.ModelForm): 
    class Meta:
        model = ConvJob
        fields = ['excel_file']