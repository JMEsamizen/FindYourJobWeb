from django.db import migrations


PLACEHOLDER_HOSTS = ("manual.example", "example.com", "seed.findyourjob.local")


def clear_placeholder_sources(apps, schema_editor):
    Vacancy = apps.get_model("jobs", "Vacancy")
    for vacancy in Vacancy.objects.all():
        urls = (vacancy.url or "", vacancy.source_url or "")
        if vacancy.channel == "seed-data" or any(host in url for url in urls for host in PLACEHOLDER_HOSTS):
            vacancy.url = None
            vacancy.source_url = None
            vacancy.source = "Demo" if vacancy.channel == "seed-data" else ""
            vacancy.is_demo = vacancy.channel == "seed-data"
            vacancy.save(update_fields=["url", "source_url", "source", "is_demo"])


class Migration(migrations.Migration):
    dependencies = [
        ("jobs", "0005_vacancy_is_demo_vacancy_source_vacancy_source_url_and_more"),
    ]

    operations = [
        migrations.RunPython(clear_placeholder_sources, migrations.RunPython.noop),
    ]
