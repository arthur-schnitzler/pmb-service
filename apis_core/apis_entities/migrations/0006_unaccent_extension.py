from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("apis_entities", "0005_alter_event_eventb_relationtype_set_and_more"),
    ]

    operations = [
        UnaccentExtension(),
    ]
