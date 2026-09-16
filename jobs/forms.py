from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Vacancy


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class ProfileForm(forms.ModelForm):
    skills_text = forms.CharField(required=False, label="Skills", widget=forms.HiddenInput())
    languages_text = forms.CharField(required=False, label="Languages", widget=forms.HiddenInput())
    class Meta:
        model = Profile
        fields = ("language", "field", "specialization", "experience_level", "work_format", "location", "experience", "education", "projects", "certifications")
        widgets = {"experience": forms.Textarea(attrs={"rows": 4}), "education": forms.Textarea(attrs={"rows": 3}), "projects": forms.Textarea(attrs={"rows": 3}), "certifications": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["skills_text"].initial = ", ".join(self.instance.skills or [])
        self.fields["languages_text"].initial = ", ".join(self.instance.languages or [])

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.skills = [item.strip().lower() for item in self.cleaned_data["skills_text"].split(",") if item.strip()]
        profile.languages = [item.strip().lower() for item in self.cleaned_data["languages_text"].split(",") if item.strip()]
        if commit:
            profile.save()
        return profile


class SearchForm(forms.Form):
    query = forms.CharField(required=False, label="Search")
    category = forms.ChoiceField(required=False, choices=[("", "Any category")] + Vacancy.CATEGORY_CHOICES)
    experience_level = forms.ChoiceField(required=False, choices=[("", "Any experience")] + Vacancy.EXPERIENCE_CHOICES)
    employment_type = forms.ChoiceField(required=False, choices=[("", "Any employment")] + Vacancy.EMPLOYMENT_CHOICES)
    work_format = forms.ChoiceField(required=False, choices=[("", "Any format")] + Vacancy.FORMAT_CHOICES)
    location = forms.CharField(required=False)
    language = forms.ChoiceField(required=False, choices=[("", "Any language"), ("en", "English"), ("ru", "Russian"), ("uz", "Uzbek")])
    salary_min = forms.IntegerField(required=False, min_value=0)
    sort = forms.ChoiceField(required=False, choices=[("newest", "Newest"), ("relevance", "Relevance"), ("salary", "Salary")], initial="newest")


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("language",)


class CVForm(forms.Form):
    TEMPLATE_CHOICES = [("modern", "Modern"), ("professional", "Professional"), ("minimal", "Minimal"), ("creative", "Creative")]
    template = forms.ChoiceField(choices=TEMPLATE_CHOICES, widget=forms.RadioSelect)
    vacancy = forms.ModelChoiceField(queryset=Vacancy.objects.all(), required=False, empty_label="No target vacancy")
