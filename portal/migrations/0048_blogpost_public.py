# Generated by Django 4.2.5 on 2023-09-21 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0047_blogpost_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='public',
            field=models.BooleanField(default=False),
        ),
    ]
