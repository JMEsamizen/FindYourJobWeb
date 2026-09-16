import json
import re
from collections import Counter
from typing import Any
from .ai import ask
from .models import Profile, Vacancy

ROLE_TERMS = {
    "programming": ("developer", "python", "javascript", "java", "backend", "frontend", "software"),
    "backend": ("backend", "бекенд", "django", "python", "server-side"),
    "frontend": ("frontend", "front-end", "javascript", "react", "фронтенд"),
    "data": ("data analyst", "data science", "analytics", "аналитик", "данн"),
    "design": ("design", "designer", "дизайн", "figma", "ui/ux"),
    "qa": ("qa", "tester", "testing", "тестиров"),
    "devops": ("devops", "docker", "kubernetes", "девопс"),
    "marketing": ("smm", "marketing", "маркетинг", "seo", "контент"),
}


def vacancy_text(vacancy: Vacancy) -> str:
    return f"{vacancy.title} {vacancy.text}".lower()


def matches_profile(vacancy: Vacancy, profile: Profile | None) -> dict[str, Any]:
    if not profile:
        return {"matched": True, "score": 0, "matched_skills": [], "missing_skills": []}
    text = vacancy_text(vacancy)
    checks = []
    if profile.field:
        terms = ROLE_TERMS.get(profile.field.lower(), (profile.field.lower(),))
        checks.append(any(term in text for term in terms))
    if profile.experience_level and profile.experience_level != "none":
        checks.append(vacancy.experience_level == profile.experience_level)
    if profile.work_format not in ("any", ""):
        requested_format = "remote" if profile.work_format == "online" else "on_site" if profile.work_format == "offline" else profile.work_format
        checks.append(vacancy.work_format == requested_format)
    if profile.location:
        checks.append(profile.location in ("remote", "worldwide") and vacancy.work_format == "remote" or profile.location.lower() in text)
    if profile.specialization:
        checks.append(profile.specialization.lower() in text or profile.specialization.lower() == vacancy.category)
    if profile.languages and vacancy.languages:
        checks.append(bool(set(profile.languages).intersection(vacancy.languages)))
    required = vacancy.skills or extract_requirements(text)
    matched = [skill for skill in required if any(skill.lower() in own.lower() for own in profile.skills)]
    missing = [skill for skill in required if skill not in matched]
    skill_score = len(matched) / len(required) * 60 if required else 0
    preference_score = sum(checks) / len(checks) * 40 if checks else 40
    score = round(skill_score + preference_score)
    return {"matched": not checks or all(checks), "score": min(score, 100), "matched_skills": matched, "missing_skills": missing, "explanation": f"Good match because you have {len(matched)} of the {len(required)} required skills."}


def recommended_vacancies(vacancies, profile):
    ranked = [(matches_profile(vacancy, profile)["score"], vacancy) for vacancy in vacancies]
    return [vacancy for _, vacancy in sorted(ranked, key=lambda item: (item[0], item[1].created_at), reverse=True)]


def extract_requirements(text: str) -> list[str]:
    known = ("python", "django", "javascript", "typescript", "react", "sql", "docker", "figma", "english", "russian", "uzbek")
    lowered = text.lower()
    return [skill for skill in known if re.search(rf"(?<![\w]){re.escape(skill)}(?![\w])", lowered)]


def fallback_analysis(vacancy: Vacancy, profile: Profile | None) -> dict[str, Any]:
    result = matches_profile(vacancy, profile)
    return {"match_percent": result["score"], "matched_skills": result["matched_skills"], "missing_skills": result["missing_skills"], "required_skills": vacancy.skills or extract_requirements(vacancy_text(vacancy)), "summary": vacancy.text[:320]}


def analyze_vacancy(vacancy: Vacancy, profile: Profile | None) -> dict[str, Any]:
    fallback = fallback_analysis(vacancy, profile)
    prompt = f"Analyze this vacancy against this profile. Return JSON with match_percent, summary, required_skills, matched_skills, missing_skills. Vacancy: {vacancy_text(vacancy)} Profile skills: {', '.join(profile.skills if profile else [])}"
    response = ask(prompt)
    if not response:
        return fallback
    try:
        value = json.loads(response)
        return {**fallback, **value}
    except (json.JSONDecodeError, TypeError):
        return fallback


def generate_cv(profile: Profile, vacancy: Vacancy | None = None) -> dict[str, Any]:
    fallback = {"summary": f"{profile.field.title()} professional focused on {profile.specialization or 'building reliable results'}.", "experience": profile.experience or "Professional experience available on request.", "projects": profile.projects or "Selected projects available on request.", "target": vacancy.title if vacancy else "General application"}
    prompt = (
        "Create a concise professional CV in plain text from these facts only. "
        f"Name: {profile.user.get_full_name() or profile.user.username}; "
        f"Field: {profile.field}; Specialization: {profile.specialization}; "
        f"Skills: {', '.join(profile.skills)}; Experience: {profile.experience}; Projects: {profile.projects}; Target vacancy: {vacancy.title if vacancy else 'none'}"
    )
    response = ask(prompt)
    if not response:
        return fallback
    try:
        value = json.loads(response)
        return {**fallback, **value}
    except (json.JSONDecodeError, TypeError):
        return fallback
