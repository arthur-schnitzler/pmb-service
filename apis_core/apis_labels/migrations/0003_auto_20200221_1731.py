# Generated by Django 2.1.2 on 2020-02-21 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("apis_labels", "0002_auto_20200121_1227"),
    ]

    operations = [
        migrations.AddField(
            model_name="label",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="label",
            name="end_date_written",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="End"
            ),
        ),
        migrations.AddField(
            model_name="label",
            name="end_end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="label",
            name="end_start_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="label",
            name="start_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="label",
            name="start_date_written",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Start"
            ),
        ),
        migrations.AddField(
            model_name="label",
            name="start_end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="label",
            name="start_start_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]