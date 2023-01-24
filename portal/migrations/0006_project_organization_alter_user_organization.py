# Generated by Django 4.1.4 on 2023-01-20 17:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0005_organization_user_organization"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                help_text="The external organization this project belongs to (optional)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="portal.organization",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                help_text="The organization this user belongs to (optional)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="users",
                to="portal.organization",
            ),
        ),
    ]
