from django.conf import settings
from django.db import models


class Profile(models.Model):
    LANGUAGE_CHOICES = [("uz", "Uzbek"), ("ru", "Russian"), ("en", "English")]
    LEVEL_CHOICES = [("none", "No experience"), ("junior", "Junior"), ("middle", "Middle"), ("senior", "Senior")]
    WORK_CHOICES = [("online", "Remote"), ("offline", "Office"), ("hybrid", "Hybrid"), ("any", "Any")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")
    FIELD_CHOICES = [(value, value.replace("_", " ").title()) for value in ("programming", "design", "data", "qa", "devops", "marketing", "sales", "support", "product", "other")]
    LOCATION_CHOICES = [(value, value.replace("_", " ").title()) for value in ("tashkent", "samarkand", "bukhara", "remote", "worldwide", "other")]
    field = models.CharField(max_length=80, blank=True, choices=FIELD_CHOICES)
    specialization = models.CharField(max_length=80, blank=True)
    skills = models.JSONField(default=list, blank=True)
    experience_level = models.CharField(max_length=30, choices=LEVEL_CHOICES, blank=True)
    work_format = models.CharField(max_length=20, choices=WORK_CHOICES, default="any")
    location = models.CharField(max_length=120, blank=True, choices=LOCATION_CHOICES)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    languages = models.JSONField(default=list, blank=True)
    certifications = models.TextField(blank=True)
    professional_summary = models.TextField(blank=True)
    cv_template = models.CharField(max_length=30, default="modern")
    cv_content = models.JSONField(default=dict, blank=True)
    cv_generations = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class Vacancy(models.Model):
    CATEGORY_CHOICES = [(value, value.replace("_", " ").title()) for value in ("programming", "design", "data", "qa", "devops", "mobile", "product", "project", "marketing", "sales", "support", "content", "other")]
    EXPERIENCE_CHOICES = [(value, value.replace("_", " ").title()) for value in ("no_experience", "junior", "middle", "senior", "lead")]
    EMPLOYMENT_CHOICES = [(value, value.replace("_", " ").title()) for value in ("full_time", "part_time", "contract", "internship", "freelance")]
    FORMAT_CHOICES = [(value, value.replace("_", " ").title()) for value in ("remote", "hybrid", "on_site")]
    url = models.URLField(unique=True)
    title = models.CharField(max_length=240)
    text = models.TextField()
    date = models.CharField(max_length=80, blank=True)
    channel = models.CharField(max_length=120, blank=True)
    company = models.CharField(max_length=160, default="FindYourJob partner")
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="other")
    skills = models.JSONField(default=list, blank=True)
    experience_level = models.CharField(max_length=30, choices=EXPERIENCE_CHOICES, default="junior")
    employment_type = models.CharField(max_length=30, choices=EMPLOYMENT_CHOICES, default="full_time")
    work_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default="remote")
    location = models.CharField(max_length=120, default="Worldwide")
    salary_min = models.PositiveIntegerField(default=0)
    salary_max = models.PositiveIntegerField(default=0)
    salary_currency = models.CharField(max_length=5, default="USD")
    languages = models.JSONField(default=list, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_jobs")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "vacancy"], name="unique_saved_job")]


class ViewedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="viewed_jobs")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "vacancy"], name="unique_viewed_job")]
        ordering = ["-viewed_at"]


class VacancyAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now=True)
