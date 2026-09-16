from collections import Counter
from django.db.models import Avg, Max, Min
from .models import Vacancy

W3SCHOOLS_URLS = {
    "python": "https://www.w3schools.com/python/",
    "django": "https://www.w3schools.com/django/",
    "javascript": "https://www.w3schools.com/js/",
    "react": "https://www.w3schools.com/react/",
    "sql": "https://www.w3schools.com/sql/",
    "html": "https://www.w3schools.com/html/",
    "css": "https://www.w3schools.com/css/",
}


def market_summary(queryset=None):
    vacancies = list((queryset or Vacancy.objects.all()).only("category", "skills", "work_format", "experience_level", "salary_min", "salary_max"))
    skill_counts = Counter(skill for vacancy in vacancies for skill in vacancy.skills)
    return {
        "total": len(vacancies),
        "skills": skill_counts.most_common(10),
        "categories": Counter(v.category for v in vacancies).most_common(),
        "formats": Counter(v.work_format for v in vacancies).most_common(),
        "levels": Counter(v.experience_level for v in vacancies).most_common(),
        "salary": Vacancy.objects.aggregate(average=Avg("salary_min"), minimum=Min("salary_min"), maximum=Max("salary_max")),
    }


def top_skills(queryset=None):
    vacancies = queryset or Vacancy.objects.all()
    counts = Counter(skill for vacancy in vacancies.only("skills") for skill in vacancy.skills)
    return [{"name": name, "demand": count, "w3schools": W3SCHOOLS_URLS.get(name.lower(), "https://www.w3schools.com/"), "youtube": f"https://www.youtube.com/results?search_query={name.replace(' ', '+')}+tutorial"} for name, count in counts.most_common(10)]
