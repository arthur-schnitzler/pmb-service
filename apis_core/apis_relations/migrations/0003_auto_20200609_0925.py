# Generated by Django 2.2.12 on 2020-06-09 09:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apis_relations', '0002_auto_20200121_1227'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventevent',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='eventwork',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='institutionevent',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='institutioninstitution',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='institutionplace',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='institutionwork',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='personevent',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='personinstitution',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='personperson',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='personplace',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='personwork',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='placeevent',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='placeplace',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='placework',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='workwork',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelManagers(
            name='eventevent',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='eventwork',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='institutionevent',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='institutioninstitution',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='institutionplace',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='institutionwork',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='personevent',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='personinstitution',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='personperson',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='personplace',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='personwork',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='placeevent',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='placeplace',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='placework',
            managers=[
            ],
        ),
        migrations.AlterModelManagers(
            name='workwork',
            managers=[
            ],
        ),
    ]
