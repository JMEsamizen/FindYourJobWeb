from django.db import migrations


def mark_missing_sources(apps, schema_editor):
    Vacancy = apps.get_model("jobs", "Vacancy")
    Vacancy.objects.filter(is_demo=False).filter(source_url__isnull=True).update(is_demo=True, source="Demo")
    Vacancy.objects.filter(is_demo=False, source_url="").update(is_demo=True, source="Demo")


class Migration(migrations.Migration):
    dependencies = [("jobs", "0007_vacancy_external_id_vacancy_updated_at_and_more")]

    operations = [migrations.RunPython(mark_missing_sources, migrations.RunPython.noop)]
