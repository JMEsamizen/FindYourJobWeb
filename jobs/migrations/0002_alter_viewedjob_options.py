from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("jobs", "0001_initial")]
    operations = [migrations.AlterModelOptions(name="viewedjob", options={"ordering": ["-viewed_at"]})]
