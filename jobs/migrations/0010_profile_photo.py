from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("jobs", "0009_classify_test_channel_as_demo")]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="photo",
            field=models.ImageField(blank=True, null=True, upload_to="profile_photos/"),
        ),
    ]