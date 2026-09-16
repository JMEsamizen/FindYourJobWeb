import io
import os
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import FileResponse, HttpResponse
from django.conf import settings
from django.utils.translation import activate, gettext
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CVForm, ProfileForm, RegisterForm, SearchForm, SettingsForm
from .models import Profile, SavedJob, Vacancy, VacancyAnalysis, ViewedJob
from .services import analyze_vacancy, generate_cv, matches_profile, recommended_vacancies
from .market import market_summary, top_skills


def get_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def home(request):
    real_vacancies = Vacancy.objects.filter(is_demo=False).exclude(source_url__isnull=True).exclude(source_url="")
    recent = real_vacancies[:6]
    recommendations = []
    if request.user.is_authenticated:
        recommendations = recommended_vacancies(real_vacancies[:100], get_profile(request.user))[:4]
    return render(request, "jobs/home.html", {"recent": recent, "recommendations": recommendations})


@login_required
def dashboard(request):
    profile_obj = get_profile(request.user)
    real_vacancies = Vacancy.objects.filter(is_demo=False).exclude(source_url__isnull=True).exclude(source_url="")
    recommendations = recommended_vacancies(real_vacancies[:100], profile_obj)[:6]
    return render(request, "jobs/dashboard.html", {"profile": profile_obj, "recommendations": recommendations, "saved_count": SavedJob.objects.filter(user=request.user).count(), "viewed": Vacancy.objects.filter(views__user=request.user).order_by("-views__viewed_at")[:4], "market": market_summary(), "skills": top_skills()[:5]})


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.create(user=user)
        login(request, user)
        return redirect("onboarding")
    return render(request, "registration/register.html", {"form": form})


def jobs(request):
    form = SearchForm(request.GET or None)
    queryset = Vacancy.objects.filter(is_demo=False).exclude(source_url__isnull=True).exclude(source_url="")
    if form.is_valid():
        query = form.cleaned_data.get("query")
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(text__icontains=query) | Q(company__icontains=query) | Q(location__icontains=query) | Q(skills__icontains=query))
        for field in ("category", "experience_level", "employment_type", "work_format"):
            if form.cleaned_data.get(field):
                queryset = queryset.filter(**{field: form.cleaned_data[field]})
        if form.cleaned_data.get("location"):
            queryset = queryset.filter(location__icontains=form.cleaned_data["location"])
        if form.cleaned_data.get("language"):
            queryset = queryset.filter(languages__contains=[form.cleaned_data["language"]])
        if form.cleaned_data.get("salary_min"):
            queryset = queryset.filter(salary_max__gte=form.cleaned_data["salary_min"])
        if form.cleaned_data.get("sort") == "salary":
            queryset = queryset.order_by(F("salary_max").desc(nulls_last=True))
        elif form.cleaned_data.get("sort") == "relevance" and query:
            queryset = queryset.order_by("-published_at", "-created_at")
    paginator = Paginator(queryset, 12)
    page = paginator.get_page(request.GET.get("page"))
    profile_obj = get_profile(request.user) if request.user.is_authenticated else None
    for vacancy in page.object_list:
        vacancy.match_result = matches_profile(vacancy, profile_obj) if profile_obj else None
    return render(request, "jobs/jobs.html", {"form": form, "page": page})


def job_detail(request, pk):
    vacancy = get_object_or_404(Vacancy.objects.filter(is_demo=False).exclude(source_url__isnull=True).exclude(source_url=""), pk=pk)
    saved = False
    analysis = None
    match_result = None
    if request.user.is_authenticated:
        ViewedJob.objects.update_or_create(user=request.user, vacancy=vacancy)
        saved = SavedJob.objects.filter(user=request.user, vacancy=vacancy).exists()
        analysis = VacancyAnalysis.objects.filter(user=request.user, vacancy=vacancy).first()
        match_result = matches_profile(vacancy, get_profile(request.user))
    return render(request, "jobs/detail.html", {"vacancy": vacancy, "saved": saved, "analysis": analysis, "match_result": match_result})


@login_required
def toggle_saved(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    saved, created = SavedJob.objects.get_or_create(user=request.user, vacancy=vacancy)
    if not created:
        saved.delete()
    return redirect("job_detail", pk=pk)


@login_required
def analyze(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    profile = get_profile(request.user)
    result = analyze_vacancy(vacancy, profile)
    VacancyAnalysis.objects.update_or_create(user=request.user, vacancy=vacancy, defaults={"result": result})
    messages.success(request, gettext("Vacancy analysis is ready."))
    return redirect("job_detail", pk=pk)


@login_required
def profile(request):
    profile_obj = get_profile(request.user)
    form = ProfileForm(request.POST or None, instance=profile_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, gettext("Profile updated."))
        return redirect("profile")
    return render(request, "jobs/profile.html", {"form": form, "profile": profile_obj})


@login_required
def onboarding(request):
    profile_obj = get_profile(request.user)
    form = ProfileForm(request.POST or None, instance=profile_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("dashboard")
    return render(request, "jobs/onboarding.html", {"form": form, "profile": profile_obj})


@login_required
def saved_jobs(request):
    page = Paginator(Vacancy.objects.filter(saved_by__user=request.user), 12).get_page(request.GET.get("page"))
    return render(request, "jobs/list.html", {"page": page, "title": gettext("Saved jobs")})


@login_required
def history(request):
    page = Paginator(Vacancy.objects.filter(views__user=request.user).order_by("-views__viewed_at"), 12).get_page(request.GET.get("page"))
    return render(request, "jobs/list.html", {"page": page, "title": gettext("Viewed history")})


@login_required
def settings_page(request):
    form = SettingsForm(request.POST or None, instance=get_profile(request.user))
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, gettext("Settings updated."))
        return redirect("settings")
    return render(request, "jobs/settings.html", {"form": form})


@login_required
def cv_builder(request):
    profile_obj = get_profile(request.user)
    form = CVForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            if profile_obj.cv_generations == 0:
                profile_obj.cv_generations = 1
            else:
                messages.info(request, gettext("Your CV was updated using the selected template and vacancy."))
            profile_obj.cv_template = form.cleaned_data["template"]
            cv_content = generate_cv(profile_obj, form.cleaned_data["vacancy"])
            profile_obj.cv_content = cv_content
            profile_obj.save(update_fields=["cv_generations", "cv_template", "cv_content", "updated_at"])
            return render(request, "jobs/cv.html", {"profile": profile_obj, "form": form, "cv_content": cv_content, "generated": True})
    return render(request, "jobs/cv.html", {"profile": profile_obj, "form": form, "generated": False})


@login_required
def cv_pdf(request):
    profile_obj = get_profile(request.user)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.setTitle(f"CV - {request.user.get_full_name() or request.user.username}")
        content = profile_obj.cv_content or generate_cv(profile_obj)
        name = request.user.get_full_name() or request.user.username
        sections = (("SUMMARY", content.get("summary", "")), ("SKILLS", ", ".join(profile_obj.skills)), ("EXPERIENCE", content.get("experience", profile_obj.experience)), ("EDUCATION", profile_obj.education), ("PROJECTS", content.get("projects", profile_obj.projects)), ("LANGUAGES", ", ".join(profile_obj.languages)), ("CERTIFICATIONS", profile_obj.certifications))
        template = profile_obj.cv_template
        if template == "modern":
            accent = colors.HexColor("#b8e36f")
            pdf.setFillColor(colors.HexColor("#17221d"))
            pdf.rect(0, 0, 155, 842, fill=1, stroke=0)
            pdf.setFillColor(accent)
            pdf.rect(155, 770, 457, 72, fill=1, stroke=0)
            pdf.setFillColor(colors.HexColor("#17221d")); pdf.setFont("Helvetica-Bold", 20); pdf.drawString(178, 800, name)
            pdf.setFillColor(colors.white); pdf.setFont("Helvetica", 9); pdf.drawString(28, 700, profile_obj.field.title()); pdf.drawString(28, 682, profile_obj.specialization)
            y = 735
            for label, value in sections:
                if not value: continue
                y -= 38; pdf.setFillColor(colors.HexColor("#17221d")); pdf.setFont("Helvetica-Bold", 9); pdf.drawString(178, y, label); pdf.setFillColor(colors.black); pdf.setFont("Helvetica", 9); pdf.drawString(178, y - 14, str(value)[:78])
        elif template == "professional":
            accent = colors.HexColor("#25332c")
            pdf.setFillColor(accent); pdf.rect(0, 765, 612, 77, fill=1, stroke=0)
            pdf.setFillColor(colors.white); pdf.setFont("Helvetica-Bold", 21); pdf.drawString(42, 806, name); pdf.setFont("Helvetica", 10); pdf.drawString(42, 787, f"{profile_obj.field.title()} | {profile_obj.specialization}")
            y = 735
            for label, value in sections:
                if not value: continue
                y -= 42; pdf.setStrokeColor(colors.HexColor("#aeb8af")); pdf.line(42, y + 12, 570, y + 12); pdf.setFillColor(accent); pdf.setFont("Helvetica-Bold", 9); pdf.drawString(42, y, label); pdf.setFillColor(colors.black); pdf.setFont("Helvetica", 9); pdf.drawString(155, y, str(value)[:76]);
                if label == "EXPERIENCE": pdf.setFillColor(colors.HexColor("#6b7d71")); pdf.circle(147, y + 3, 3, fill=1, stroke=0)
        elif template == "minimal":
            pdf.setFillColor(colors.black); pdf.setFont("Helvetica-Bold", 22); pdf.drawString(54, 780, name); pdf.setStrokeColor(colors.HexColor("#aeb8af")); pdf.line(54, 758, 558, 758); pdf.setFillColor(colors.HexColor("#555b57")); pdf.setFont("Helvetica", 9); pdf.drawString(54, 740, f"{profile_obj.field.title()}  /  {profile_obj.specialization}")
            y = 700
            for label, value in sections:
                if not value: continue
                y -= 46; pdf.setFillColor(colors.HexColor("#555b57")); pdf.setFont("Helvetica-Bold", 8); pdf.drawString(54, y, label); pdf.setFillColor(colors.black); pdf.setFont("Helvetica", 9); pdf.drawString(54, y - 16, str(value)[:96]);
        else:
            coral = colors.HexColor("#d9654f"); yellow = colors.HexColor("#e6c85c"); ink = colors.HexColor("#17221d")
            pdf.setFillColor(coral); pdf.rect(0, 0, 28, 842, fill=1, stroke=0); pdf.setFillColor(yellow); pdf.rect(420, 760, 192, 82, fill=1, stroke=0); pdf.setFillColor(ink); pdf.rect(48, 750, 335, 70, fill=1, stroke=0)
            pdf.setFillColor(colors.white); pdf.setFont("Helvetica-Bold", 21); pdf.drawString(66, 783, name); pdf.setFont("Helvetica", 9); pdf.drawString(66, 766, profile_obj.specialization)
            y = 710
            for index, (label, value) in enumerate(sections):
                if not value: continue
                y -= 42; pdf.setFillColor(yellow if index % 2 == 0 else coral); pdf.rect(48, y - 7, 94, 19, fill=1, stroke=0); pdf.setFillColor(ink); pdf.setFont("Helvetica-Bold", 8); pdf.drawString(56, y, label); pdf.setFillColor(colors.black); pdf.setFont("Helvetica", 9); pdf.drawString(160, y, str(value)[:78])
        pdf.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="findyourjob-cv.pdf")
    except ImportError:
        return HttpResponse("Install reportlab to export PDF.", status=500)


def about(request):
    return render(request, "jobs/about.html")


def market(request):
    return render(request, "jobs/market.html", {"summary": market_summary(), "skills": top_skills()})


def learn(request, skill):
    from urllib.parse import quote_plus
    return redirect(f"https://www.youtube.com/results?search_query={quote_plus(skill + ' tutorial')}")


def language_switch(request):
    language = request.POST.get("language") or request.GET.get("language", "en")
    if language not in {"en", "ru", "uz"}:
        language = "en"
    activate(language)
    request.LANGUAGE_CODE = language
    request.session["language"] = language
    if request.user.is_authenticated:
        profile_obj = get_profile(request.user)
        profile_obj.language = language
        profile_obj.save(update_fields=["language", "updated_at"])
    response = redirect(request.POST.get("next") or request.GET.get("next") or "home")
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language, max_age=31536000, samesite="Lax")
    return response
