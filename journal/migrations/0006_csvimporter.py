# Generated by Django 4.2.18 on 2025-03-03 23:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0008_alter_task_type"),
        ("journal", "0005_csvexporter"),
    ]

    operations = [
        migrations.CreateModel(
            name="CsvImporter",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("users.task",),
        ),
    ]
