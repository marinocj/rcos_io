# Generated by Django 4.2.2 on 2023-09-06 23:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0041_organization_logo_url_alter_project_is_approved_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meeting',
            name='room',
            field=models.ForeignKey(blank=True, help_text='Physical location of the meeting, or blank if on Discord', null=True, on_delete=django.db.models.deletion.RESTRICT, to='portal.room'),
        ),
        migrations.AlterField(
            model_name='meeting',
            name='type',
            field=models.CharField(choices=[('small_group', 'Small Group'), ('large_group', 'Large Group'), ('workshop', 'Workshop'), ('office_hours', 'Office Hours'), ('mentor', 'Mentor'), ('coordinator', 'Coordinator')], default='small_group', max_length=100),
        ),
    ]