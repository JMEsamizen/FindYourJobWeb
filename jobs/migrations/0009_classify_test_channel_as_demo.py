from django.db import migrations


def classify_test_channel(apps, schema_editor):
    Vacancy = apps.get_model("jobs", "Vacancy")
    Vacancy.objects.filter(channel="testjobs4224").update(
        is_demo=True,
        source="Demo",
        source_url=None,
        url=None,
        external_id=None,
    )


class Migration(migrations.Migration):
    dependencies = [("jobs", "0008_mark_missing_sources_as_demo")]

    operations = [migrations.RunPython(classify_test_channel, migrations.RunPython.noop)]