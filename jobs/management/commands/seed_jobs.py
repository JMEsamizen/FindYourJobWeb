from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from jobs.models import Vacancy


ROLES = [
    ("Python Developer", "programming", ["python", "git", "sql"]),
    ("Django Developer", "programming", ["python", "django", "postgresql"]),
    ("Frontend Developer", "programming", ["javascript", "react", "css"]),
    ("Backend Developer", "programming", ["python", "api", "docker"]),
    ("Full Stack Developer", "programming", ["javascript", "python", "postgresql"]),
    ("Java Developer", "programming", ["java", "spring", "sql"]),
    ("QA Engineer", "qa", ["testing", "selenium", "api"]),
    ("UI/UX Designer", "design", ["figma", "research", "prototyping"]),
    ("Graphic Designer", "design", ["figma", "illustrator", "branding"]),
    ("Data Analyst", "data", ["sql", "python", "tableau"]),
    ("Data Scientist", "data", ["python", "machine learning", "pandas"]),
    ("DevOps Engineer", "devops", ["docker", "kubernetes", "linux"]),
    ("Mobile Developer", "mobile", ["flutter", "dart", "mobile"]),
    ("Flutter Developer", "mobile", ["flutter", "dart", "firebase"]),
    ("Android Developer", "mobile", ["kotlin", "android", "git"]),
    ("Product Manager", "product", ["roadmap", "analytics", "research"]),
    ("Project Manager", "project", ["agile", "jira", "planning"]),
    ("SMM Specialist", "marketing", ["smm", "content", "analytics"]),
    ("SEO Specialist", "marketing", ["seo", "content", "analytics"]),
    ("Content Manager", "content", ["content", "copywriting", "seo"]),
    ("Marketing Specialist", "marketing", ["marketing", "crm", "analytics"]),
    ("Sales Manager", "sales", ["sales", "crm", "negotiation"]),
    ("Customer Support Specialist", "support", ["support", "communication", "english"]),
    ("Technical Writer", "content", ["writing", "documentation", "english"]),
]
COMPANIES = ["Nova Labs", "Silk Road Tech", "BrightWorks", "Cloud Avenue", "North Star", "Orbit Systems"]
LEVELS = ["no_experience", "junior", "middle", "senior", "lead"]
FORMATS = ["remote", "hybrid", "on_site"]
LOCATIONS = ["Tashkent", "Samarkand", "Bukhara", "Almaty", "Remote worldwide"]
EMPLOYMENT = ["full_time", "part_time", "contract", "internship", "freelance"]


class Command(BaseCommand):
    help = "Create 120 varied, idempotent seed vacancies for initial development data."

    def handle(self, *args, **options):
        created = 0
        now = timezone.now()
        for index in range(120):
            role, category, skills = ROLES[index % len(ROLES)]
            level = LEVELS[index % len(LEVELS)]
            work_format = FORMATS[index % len(FORMATS)]
            employment = EMPLOYMENT[index % len(EMPLOYMENT)]
            location = LOCATIONS[index % len(LOCATIONS)]
            company = COMPANIES[index % len(COMPANIES)]
            title = f"{role} - {level.replace('_', ' ').title()} #{index + 1}"
            url = f"https://seed.findyourjob.local/vacancy/{index + 1}"
            description = f"{company} is looking for a {role} to join a practical team. You will work on customer-facing projects, collaborate with colleagues, and improve reliable products. Required skills: {', '.join(skills)}."
            _, was_created = Vacancy.objects.update_or_create(url=url, defaults={
                "title": title, "text": description, "date": (now - timedelta(days=index % 30)).date().isoformat(),
                "channel": "seed-data", "company": company, "category": category, "skills": skills,
                "experience_level": level, "employment_type": employment, "work_format": work_format,
                "location": location, "salary_min": 500 + (index % 8) * 250, "salary_max": 1100 + (index % 8) * 400,
                "salary_currency": "USD", "languages": ["en"] if index % 3 else ["en", "ru"],
                "published_at": now - timedelta(days=index % 30),
            })
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} new vacancies; 120 deterministic records are now available."))
