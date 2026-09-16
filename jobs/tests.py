from django.contrib.auth.models import User
from django.test import TestCase
from django.core.management import call_command
from .views import profile_completion
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO
from unittest.mock import patch
import httpx
from .models import Profile, Vacancy, VacancyAnalysis
from .importer import import_item, import_telegram_channels
from .sources.telegram import VacancySourceItem
from .services import fallback_analysis, matches_profile, recommended_vacancies


class MatchingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alex", password="pass12345")
        self.profile = Profile.objects.create(user=self.user, field="programming", skills=["python", "django"], work_format="remote")
        self.good = Vacancy.objects.create(url="https://t.me/kasbim_uz/101", source_url="https://t.me/kasbim_uz/101", external_id="kasbim_uz/101", source="Telegram", title="Python backend remote", text="Backend Python Django remote role", skills=["python", "django"], category="programming", work_format="remote")
        self.other = Vacancy.objects.create(url="https://t.me/kasbim_uz/102", source_url="https://t.me/kasbim_uz/102", external_id="kasbim_uz/102", source="Telegram", title="Graphic designer", text="Figma and branding in office", skills=["figma"], category="design", work_format="on_site")

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

    def test_jobs_default_listing_shows_real_vacancies(self):
        response = self.client.get(reverse("jobs"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.good.title)
        self.assertContains(response, "jobs found")

    def test_jobs_query_alias_and_combined_filters(self):
        response = self.client.get(reverse("jobs"), {"q": "Python", "role": "programming", "level": "junior", "format": "remote"})
        self.assertContains(response, self.good.title)
        self.assertNotContains(response, self.other.title)
        self.assertContains(response, "q=Python")

    def test_jobs_sort_and_invalid_parameters_are_safe(self):
        for params in ({"sort": "oldest"}, {"sort": "not-a-sort"}, {"salary_min": "invalid"}, {"page": "invalid"}):
            self.assertEqual(self.client.get(reverse("jobs"), params).status_code, 200)

    def test_relevance_sort_prioritizes_title_match(self):
        response = self.client.get(reverse("jobs"), {"query": "Python", "sort": "relevance"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["page"])[0], self.good)

    def _image_upload(self, name="avatar.png", color=(36, 37, 130)):
        output = BytesIO()
        Image.new("RGB", (32, 32), color).save(output, format="PNG")
        return SimpleUploadedFile(name, output.getvalue(), content_type="image/png")

    def test_profile_photo_upload_replace_remove_and_invalid_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("profile"), {"photo_action": "1", "photo": self._image_upload()})
        self.assertRedirects(response, reverse("profile"))
        self.profile.refresh_from_db()
        first_photo = self.profile.photo.name
        self.assertTrue(first_photo.startswith("profile_photos/"))
        self.client.post(reverse("profile"), {"photo_action": "1", "photo": self._image_upload("second.png", (246, 76, 114))})
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.photo.name, first_photo)
        invalid = self.client.post(reverse("profile"), {"photo_action": "1", "photo": SimpleUploadedFile("avatar.txt", b"not image", content_type="text/plain")})
        self.assertEqual(invalid.status_code, 200)
        self.client.post(reverse("profile"), {"photo_action": "1", "remove_photo": "on"})
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.photo)

    def test_history_is_user_scoped_deduplicated_ordered_and_clearable(self):
        second = Vacancy.objects.create(url="https://t.me/kasbim_uz/103", source_url="https://t.me/kasbim_uz/103", external_id="kasbim_uz/103", source="Telegram", title="Second job", text="Second", category="programming")
        self.client.force_login(self.user)
        self.client.get(reverse("job_detail", args=[self.good.pk]))
        self.client.get(reverse("job_detail", args=[second.pk]))
        self.client.get(reverse("job_detail", args=[self.good.pk]))
        self.assertEqual(self.user.viewed_jobs.count(), 2)
        history_response = self.client.get(reverse("history"))
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(list(history_response.context["page"])[0], self.good)
        other_user = User.objects.create_user(username="other", password="pass12345")
        self.client.force_login(other_user)
        self.assertNotContains(self.client.get(reverse("history")), self.good.title)
        self.client.force_login(self.user)
        self.assertRedirects(self.client.post(reverse("clear_history")), reverse("history"))
        self.assertEqual(self.user.viewed_jobs.count(), 0)

    def test_profile_completion_reaches_100_with_all_required_fields(self):
        self.profile.field = "programming"
        self.profile.specialization = "Backend"
        self.profile.skills = ["python"]
        self.profile.experience_level = "junior"
        self.profile.work_format = "remote"
        self.profile.location = "tashkent"
        self.profile.experience = "One year"
        self.profile.education = "Computer science"
        self.profile.languages = ["en"]
        self.profile.save()
        completion, missing = profile_completion(self.profile)
        self.assertEqual(completion, 100)
        self.assertEqual(missing, [])
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("dashboard")), "100%")

    def test_cv_templates_have_distinct_previews_and_exports(self):
        self.client.force_login(self.user)
        previews = []
        pdfs = []
        for template in ("modern", "professional", "minimal", "creative"):
            response = self.client.post(reverse("cv_builder"), {"template": template, "vacancy": self.good.pk})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f"cv-{template}")
            previews.append(response.content)
            pdf_response = self.client.get(reverse("cv_pdf"))
            pdfs.append(b"".join(pdf_response.streaming_content))
        self.assertEqual(len(set(previews)), 4)
        self.assertEqual(len(set(pdfs)), 4)

    def test_original_source_link_is_rendered(self):
        response = self.client.get(reverse("job_detail", args=[self.good.pk]))
        self.assertContains(response, 'href="https://t.me/kasbim_uz/101"')
        self.assertContains(response, "View original vacancy")

    def test_vacancies_without_source_are_hidden_from_production(self):
        unavailable = Vacancy.objects.create(title="No source", text="No source", source="", category="other")
        response = self.client.get(reverse("jobs"))
        self.assertNotContains(response, unavailable.title)
        self.assertEqual(self.client.get(reverse("job_detail", args=[unavailable.pk])).status_code, 404)

    def test_import_creates_and_updates_by_source_external_id(self):
        item = VacancySourceItem("channel/7", "Original title", "Original text", "2026-09-16", "Telegram", "https://t.me/channel/7", "channel")
        vacancy, created = import_item(item)
        self.assertTrue(created)
        self.assertEqual(vacancy.source_url, item.source_url)
        updated_item = VacancySourceItem(item.external_id, "Updated title", "Updated text", item.date, item.source, item.source_url, item.channel)
        updated, created = import_item(updated_item)
        self.assertFalse(created)
        self.assertEqual(updated.pk, vacancy.pk)
        self.assertEqual(Vacancy.objects.filter(source="Telegram", external_id="channel/7").count(), 1)
        self.assertEqual(updated.title, "Updated title")

    @patch("jobs.importer.fetch_channel", side_effect=httpx.ConnectError("offline"))
    def test_one_source_error_does_not_abort_import(self, fetch_channel):
        created, updated, errors = import_telegram_channels(["unavailable-channel"])
        self.assertEqual((created, updated), (0, 0))
        self.assertEqual(len(errors), 1)

    def test_language_switch_sets_django_cookie(self):
        response = self.client.post(reverse("language_switch"), {"language": "ru", "next": reverse("home")})
        self.assertEqual(response.cookies["django_language"].value, "ru")

    def test_seed_command_is_idempotent(self):
        call_command("seed_jobs")
        first_count = Vacancy.objects.filter(channel="seed-data").count()
        call_command("seed_jobs")
        self.assertEqual(first_count, 120)
        self.assertEqual(Vacancy.objects.filter(channel="seed-data").count(), first_count)
        self.assertEqual(Vacancy.objects.filter(channel="seed-data", is_demo=True, source_url__isnull=True).count(), 120)

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
