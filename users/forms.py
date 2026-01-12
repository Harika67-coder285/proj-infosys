from django import forms
from .models import Freelancer

class FreelancerForm(forms.ModelForm):
    class Meta:
        model = Freelancer
        fields = [
            'full_name',
            'job_role',
            'experience_level',
            'skills',
            'tech_stack',
            'hourly_rate',
            'location',
            'education',
            'phone',
            'dob',
            'address',
            'linkedin',
            'resume',
            'photo'
        ]

        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
from django import forms
from .models import Recruiter

from django import forms
from .models import Recruiter
from django.contrib.auth.hashers import make_password

class RecruiterSettingsForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        required=False
    )

    class Meta:
        model = Recruiter
        fields = ['full_name', 'email', 'is_active']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def save(self, commit=True):
        recruiter = super().save(commit=False)

        password = self.cleaned_data.get('password')
        if password:
            recruiter.password = make_password(password)  # ✅ HASHED

        if commit:
            recruiter.save()

        return recruiter
