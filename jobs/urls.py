from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"), path("dashboard/", views.dashboard, name="dashboard"), path("register/", views.register, name="register"),
    path("jobs/", views.jobs, name="jobs"), path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/save/", views.toggle_saved, name="toggle_saved"), path("jobs/<int:pk>/analyze/", views.analyze, name="analyze"),
    path("profile/", views.profile, name="profile"), path("onboarding/", views.onboarding, name="onboarding"), path("saved/", views.saved_jobs, name="saved_jobs"),
    path("history/", views.history, name="history"), path("history/clear/", views.clear_history, name="clear_history"), path("settings/", views.settings_page, name="settings"),
    path("cv/", views.cv_builder, name="cv_builder"), path("cv/pdf/", views.cv_pdf, name="cv_pdf"),
    path("about/", views.about, name="about"), path("market/", views.market, name="market"), path("learn/<str:skill>/", views.learn, name="learn"), path("language/", views.language_switch, name="language_switch"),
]
