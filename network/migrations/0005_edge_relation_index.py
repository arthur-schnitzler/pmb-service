from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("network", "0004_alter_edge_source_lat_alter_edge_source_lng_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="edge",
            index=models.Index(fields=["edge_kind", "edge_id"], name="edge_relation_idx"),
        ),
    ]
