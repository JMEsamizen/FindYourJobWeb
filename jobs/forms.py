from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Profile, Vacancy


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control auth-input", "placeholder": "you@example.com"}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control auth-input", "placeholder": "your_username"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control auth-input", "placeholder": "********"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control auth-input", "placeholder": "********"}),
        }


class ProfileForm(forms.ModelForm):
    skills_text = forms.CharField(required=False, label="Skills", widget=forms.HiddenInput())
    languages_text = forms.CharField(required=False, label="Languages", widget=forms.HiddenInput())

    class Meta:
        model = Profile
        fields = ("language", "field", "specialization", "experience_level", "work_format", "location", "experience", "education", "projects", "certifications")
        widgets = {
            "language": forms.Select(attrs={"class": "form-select"}),
            "field": forms.Select(attrs={"class": "form-select"}),
            "specialization": forms.TextInput(attrs={"class": "form-control"}),
            "experience_level": forms.Select(attrs={"class": "form-select"}),
            "work_format": forms.Select(attrs={"class": "form-select"}),
            "location": forms.Select(attrs={"class": "form-select"}),
            "experience": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "education": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "projects": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "certifications": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

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


class ProfilePhotoForm(forms.ModelForm):
    remove_photo = forms.BooleanField(required=False, label=_("Remove photo"))

    class Meta:
        model = Profile
        fields = ("photo",)
        widgets = {"photo": forms.ClearableFileInput(attrs={"accept": "image/*"})}

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo and photo.size > 5 * 1024 * 1024:
            raise ValidationError(_("Image must be 5 MB or smaller."))
        if photo and hasattr(photo, "content_type") and photo.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise ValidationError(_("Upload a JPG, PNG, or WebP image."))
        return photo

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.cleaned_data.get("remove_photo"):
            profile.photo.delete(save=False)
            profile.photo = None
        if commit:
            profile.save()
        return profile


class SearchForm(forms.Form):
    query = forms.CharField(required=False, label=_("Search"), widget=forms.TextInput(attrs={"placeholder": _("Search jobs, skills, companies..."), "aria-label": _("Search jobs, skills, companies..."), "class": "form-control"}))
    category = forms.ChoiceField(required=False, choices=[("", _("Any role"))] + [(value, _(label)) for value, label in Vacancy.CATEGORY_CHOICES], widget=forms.Select(attrs={"class": "form-select"}))
    experience_level = forms.ChoiceField(required=False, choices=[("", _("Any level"))] + [(value, _(label)) for value, label in Vacancy.EXPERIENCE_CHOICES], widget=forms.Select(attrs={"class": "form-select"}))
    employment_type = forms.ChoiceField(required=False, choices=[("", _("Any employment"))] + [(value, _(label)) for value, label in Vacancy.EMPLOYMENT_CHOICES], widget=forms.Select(attrs={"class": "form-select"}))
    work_format = forms.ChoiceField(required=False, choices=[("", _("Any format"))] + [(value, _(label)) for value, label in Vacancy.FORMAT_CHOICES], widget=forms.Select(attrs={"class": "form-select"}))
    location = forms.ChoiceField(required=False, choices=[("", _("Any location"))], widget=forms.Select(attrs={"class": "form-select"}))
    language = forms.ChoiceField(required=False, choices=[("", _("Any language")), ("en", _("English")), ("ru", _("Russian")), ("uz", _("Uzbek"))], widget=forms.Select(attrs={"class": "form-select"}))
    source = forms.ChoiceField(required=False, choices=[("", _("Any source"))], widget=forms.Select(attrs={"class": "form-select"}))
    salary_min = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    sort = forms.ChoiceField(required=False, choices=[("newest", "Newest"), ("oldest", "Oldest"), ("relevance", "Relevance"), ("salary", "Salary")], initial="newest", widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, locations=None, sources=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location"].choices += [(value, value) for value in locations or []]
        self.fields["source"].choices += [(value, value) for value in sources or []]


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("language",)
        widgets = {"language": forms.Select(attrs={"class": "form-select"})}


class CVForm(forms.Form):
    TEMPLATE_CHOICES = [("modern", "Modern"), ("professional", "Professional"), ("minimal", "Minimal"), ("creative", "Creative")]
    template = forms.ChoiceField(choices=TEMPLATE_CHOICES, widget=forms.RadioSelect(attrs={"class": "cv-template-radio"}))
    vacancy = forms.ModelChoiceField(queryset=Vacancy.objects.all(), required=False, empty_label="No target vacancy", widget=forms.Select(attrs={"class": "form-select"}))
