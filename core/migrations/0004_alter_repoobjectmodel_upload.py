# Generated by Django 5.2 on 2025-05-03 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_repoobjectmodel_repo_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repoobjectmodel',
            name='upload',
            field=models.BinaryField(),
        ),
    ]
