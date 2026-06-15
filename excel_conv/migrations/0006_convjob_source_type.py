from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("excel_conv", "0005_alter_convjob_upload_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="convjob",
            name="source_type",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
    ]
