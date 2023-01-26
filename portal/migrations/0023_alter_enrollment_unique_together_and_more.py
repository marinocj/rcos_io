# Generated by Django 4.1.4 on 2023-01-26 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0022_enrollment_portal_enro_user_id_794ee8_idx_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="enrollment",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="meetingattendance",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="meetingattendancecode",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="projectpitch",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="projectpresentation",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="projectproposal",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="enrollment",
            constraint=models.UniqueConstraint(
                fields=("semester", "user"), name="unique_semester_enrollment"
            ),
        ),
        migrations.AddConstraint(
            model_name="meetingattendance",
            constraint=models.UniqueConstraint(
                fields=("meeting", "user"), name="unique_meeting_attendance"
            ),
        ),
        migrations.AddConstraint(
            model_name="meetingattendancecode",
            constraint=models.UniqueConstraint(
                fields=("code", "meeting", "small_group"),
                name="unique_meeting_attendance_small_group_code",
            ),
        ),
        migrations.AddConstraint(
            model_name="mentorapplication",
            constraint=models.UniqueConstraint(
                fields=("semester", "user"), name="unique_mentor_application"
            ),
        ),
        migrations.AddConstraint(
            model_name="projectenrollmentapplication",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_accepted", True)),
                fields=("semester", "user"),
                name="unique_accepted_application",
            ),
        ),
        migrations.AddConstraint(
            model_name="projectpitch",
            constraint=models.UniqueConstraint(
                fields=("semester", "project"), name="unique_semester_pitch"
            ),
        ),
        migrations.AddConstraint(
            model_name="projectpresentation",
            constraint=models.UniqueConstraint(
                fields=("semester", "project"), name="unique_semester_presentation"
            ),
        ),
        migrations.AddConstraint(
            model_name="projectproposal",
            constraint=models.UniqueConstraint(
                fields=("semester", "project"), name="unique_semester_proposal"
            ),
        ),
    ]