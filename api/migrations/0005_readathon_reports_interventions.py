# Generated for E-Readathon report history and intervention notes
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_profile_reporting_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReadathonReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('report_type', models.CharField(choices=[('parent', 'Parent Report'), ('teacher', 'Teacher Insight')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('recipient_email', models.EmailField(blank=True, max_length=254)),
                ('delivery_status', models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('failed', 'Failed')], default='draft', max_length=20)),
                ('emailed_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='readathon_reports', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InterventionNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(default='Reading Intervention', max_length=255)),
                ('note', models.TextField()),
                ('status', models.CharField(default='open', max_length=30)),
                ('priority', models.CharField(default='medium', max_length=30)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='readathon_interventions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
