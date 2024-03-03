# Generated by Django 5.0.1 on 2024-03-01 14:24

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("apis_entities", "0002_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="event",
            options={
                "ordering": ["id"],
                "verbose_name": "Ereignis",
                "verbose_name_plural": "Ereignisse",
            },
        ),
        migrations.AlterModelOptions(
            name="institution",
            options={
                "ordering": ["id"],
                "verbose_name": "Institution",
                "verbose_name_plural": "Institutionen",
            },
        ),
        migrations.AlterModelOptions(
            name="person",
            options={
                "ordering": ["id"],
                "verbose_name": "Person",
                "verbose_name_plural": "Personen",
            },
        ),
        migrations.AlterModelOptions(
            name="place",
            options={
                "ordering": ["id"],
                "verbose_name": "Ort",
                "verbose_name_plural": "Orte",
            },
        ),
        migrations.AlterModelOptions(
            name="work",
            options={
                "ordering": ["id"],
                "verbose_name": "Werk",
                "verbose_name_plural": "Werke",
            },
        ),
    ]
