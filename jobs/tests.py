from django.contrib.auth.models import User
from django.test import TestCase
from django.core.management import call_command
from django.urls import reverse
from .models import Profile, Vacancy, VacancyAnalysis
from .services import fallback_analysis, matches_profile, recommended_vacancies


class MatchingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alex", password="pass12345")
        self.profile = Profile.objects.create(user=self.user, field="programming", skills=["python", "django"], work_format="remote")
        self.good = Vacancy.objects.create(url="https://example.com/good", title="Python backend remote", text="Backend Python Django remote role", skills=["python", "django"], category="programming", work_format="remote")
        self.other = Vacancy.objects.create(url="https://example.com/other", title="Graphic designer", text="Figma and branding in office", skills=["figma"], category="design", work_format="on_site")

    def test_matching_scores_and_recommendations(self):
        self.assertGreater(matches_profile(self.good, self.profile)["score"], matches_profile(self.other, self.profile)["score"])
        self.assertEqual(recommended_vacancies(Vacancy.objects.all(), self.profile)[0], self.good)

    def test_analysis_has_required_fields(self):
        result = fallback_analysis(self.good, self.profile)
        self.assertIn("required_skills", result)
        self.assertIn("match_percent", result)

    def test_search_filters_structured_fields(self):
        response = self.client.get(reverse("jobs"), {"category": "programming", "work_format": "remote", "query": "Python"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.good.title)
        self.assertNotContains(response, self.other.title)

    def test_language_switch_sets_django_cookie(self):
        response = self.client.post(reverse("language_switch"), {"language": "ru", "next": reverse("home")})
        self.assertEqual(response.cookies["django_language"].value, "ru")

    def test_seed_command_is_idempotent(self):
        call_command("seed_jobs")
        first_count = Vacancy.objects.filter(channel="seed-data").count()
        call_command("seed_jobs")
        self.assertEqual(first_count, 120)
        self.assertEqual(Vacancy.objects.filter(channel="seed-data").count(), first_count)

    def test_authenticated_product_flows(self):
        self.client.force_login(self.user)
        for url_name in ("dashboard", "jobs", "market", "profile", "onboarding", "cv_builder"):
            self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)
        detail = self.client.get(reverse("job_detail", args=[self.good.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertTrue(self.user.viewed_jobs.filter(vacancy=self.good).exists())
        self.client.post(reverse("toggle_saved", args=[self.good.pk]))
        self.assertTrue(self.user.saved_jobs.filter(vacancy=self.good).exists())
        self.client.post(reverse("analyze", args=[self.good.pk]))
        self.assertTrue(VacancyAnalysis.objects.filter(user=self.user, vacancy=self.good).exists())
        response = self.client.post(reverse("cv_builder"), {"template": "modern", "vacancy": self.good.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Professional summary")
        self.assertEqual(self.client.get(reverse("cv_pdf")).status_code, 200)

    def test_registration_redirects_to_onboarding(self):
        self.client.logout()
        response = self.client.post(reverse("register"), {"username": "new-user", "email": "new@example.com", "password1": "StrongPass123!", "password2": "StrongPass123!"})
        self.assertRedirects(response, reverse("onboarding"))

    def test_language_switch_persists_translated_navbar(self):
        self.client = self.client_class(HTTP_HOST="localhost")
        for language, marker in (("ru", "Вакансии"), ("uz", "Vakansiyalar"), ("en", "Jobs")):
            self.client.post(reverse("language_switch"), {"language": language, "next": reverse("home")})
            response = self.client.get(reverse("home"))
            self.assertEqual(response.wsgi_request.LANGUAGE_CODE, language)
            self.assertContains(response, marker)

    def test_cv_fallback_is_saved_and_pdf_is_downloadable(self):
        self.client.force_login(self.user)
        form_page = self.client.get(reverse("cv_builder"))
        self.assertContains(form_page, '<form method="post"')
        self.assertContains(form_page, 'name="template"')
        self.assertContains(form_page, 'name="vacancy"')
        self.assertNotContains(form_page, "disabled")
        response = self.client.post(reverse("cv_builder"), {"template": "creative", "vacancy": self.good.pk})
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.cv_template, "creative")
        self.assertTrue(self.profile.cv_content.get("summary"))
        pdf = self.client.get(reverse("cv_pdf"))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")

    def test_cv_form_posts_all_templates_with_vacancy(self):
        self.client.force_login(self.user)
        form_page = self.client.get(reverse("cv_builder"))
        for template in ("modern", "professional", "minimal", "creative"):
            self.assertContains(form_page, f'value="{template}"')
        for template in ("modern", "professional", "minimal", "creative"):
            response = self.client.post(reverse("cv_builder"), {"template": template, "vacancy": self.good.pk})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Professional summary")
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.cv_template, template)
            self.assertEqual(self.profile.cv_content.get("target"), self.good.title)

    def test_pdf_design_changes_with_template(self):
        self.client.force_login(self.user)
        pdfs = []
        for template in ("modern", "professional", "minimal", "creative"):
            self.client.post(reverse("cv_builder"), {"template": template, "vacancy": self.good.pk})
            pdf_response = self.client.get(reverse("cv_pdf"))
            pdfs.append(b"".join(pdf_response.streaming_content))
        self.assertEqual(len(set(pdfs)), 4)
