# Generated by Django 2.1.12 on 2020-01-21 12:27

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(blank=True, help_text='The entities label or name.', max_length=255)),
                ('isocode_639_3', models.CharField(blank=True, default='deu', help_text="The ISO 639-3 (or 2) code for the label's language.", max_length=3, null=True, verbose_name='ISO Code')),
            ],
        ),
    ]
