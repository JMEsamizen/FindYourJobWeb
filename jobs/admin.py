from django.contrib import admin
from .models import Profile, Vacancy, SavedJob, ViewedJob, VacancyAnalysis

admin.site.register([Profile, Vacancy, SavedJob, ViewedJob, VacancyAnalysis])
