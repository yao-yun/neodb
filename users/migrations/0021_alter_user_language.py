# Generated by Django 4.2.13 on 2024-06-02 19:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0020_user_language"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="language",
            field=models.CharField(
                choices=[
                    ("en", "English"),
                    ("zh-hans", "Simplified Chinese"),
                    ("zh-hant", "Traditional Chinese"),
                ],
                default="en",
                max_length=10,
                verbose_name="language",
            ),
        ),
    ]
