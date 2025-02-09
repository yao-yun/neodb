# Generated by Django 4.2.18 on 2025-02-09 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_task_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='SteamImporter',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('users.task',),
        ),
        migrations.AlterField(
            model_name='task',
            name='type',
            field=models.CharField(choices=[('journal.csvexporter', 'csv exporter'), ('journal.doubanimporter', 'douban importer'), ('journal.doufenexporter', 'doufen exporter'), ('journal.goodreadsimporter', 'goodreads importer'), ('journal.letterboxdimporter', 'letterboxd importer'), ('journal.ndjsonexporter', 'ndjson exporter'), ('users.steamimporter', 'steam importer')], db_index=True, max_length=255),
        ),
    ]
