# Generated by Django 5.1.3 on 2024-12-09 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("network", "0003_edge_source_lat_edge_source_lng_edge_target_lat_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="edge",
            name="source_lat",
            field=models.FloatField(
                blank=True, null=True, verbose_name="Breitengrad (Start)"
            ),
        ),
        migrations.AlterField(
            model_name="edge",
            name="source_lng",
            field=models.FloatField(
                blank=True, null=True, verbose_name="Längengrad (Start)"
            ),
        ),
        migrations.AlterField(
            model_name="edge",
            name="target_lat",
            field=models.FloatField(
                blank=True, null=True, verbose_name="Breitengrad (Ziel)"
            ),
        ),
        migrations.AlterField(
            model_name="edge",
            name="target_lng",
            field=models.FloatField(
                blank=True, null=True, verbose_name="Längengrad (Ziel)"
            ),
        ),
    ]
