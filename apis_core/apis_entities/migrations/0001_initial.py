# Generated by Django 2.1.12 on 2020-01-21 12:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("apis_metainfo", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "tempentityclass_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="apis_metainfo.TempEntityClass",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("apis_metainfo.tempentityclass",),
        ),
        migrations.CreateModel(
            name="Institution",
            fields=[
                (
                    "tempentityclass_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="apis_metainfo.TempEntityClass",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("apis_metainfo.tempentityclass",),
        ),
        migrations.CreateModel(
            name="Person",
            fields=[
                (
                    "tempentityclass_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="apis_metainfo.TempEntityClass",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True,
                        help_text="The persons´s forename. In case of more then one name...",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[("female", "female"), ("male", "male")],
                        max_length=15,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("apis_metainfo.tempentityclass",),
        ),
        migrations.CreateModel(
            name="Place",
            fields=[
                (
                    "tempentityclass_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="apis_metainfo.TempEntityClass",
                    ),
                ),
                (
                    "lat",
                    models.FloatField(blank=True, null=True, verbose_name="latitude"),
                ),
                (
                    "lng",
                    models.FloatField(blank=True, null=True, verbose_name="longitude"),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("apis_metainfo.tempentityclass",),
        ),
        migrations.CreateModel(
            name="Work",
            fields=[
                (
                    "tempentityclass_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="apis_metainfo.TempEntityClass",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("apis_metainfo.tempentityclass",),
        ),
    ]
