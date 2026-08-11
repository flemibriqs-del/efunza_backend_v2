# Generated patch for E-Readathon parent/teacher report preferences

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_book_text_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='parent_name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='profile',
            name='parent_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='teacher_name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='profile',
            name='teacher_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='auto_parent_reports',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='auto_teacher_reports',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='report_frequency',
            field=models.CharField(blank=True, default='weekly', max_length=20),
        ),
    ]
