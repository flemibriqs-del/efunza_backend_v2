# E-Readathon Backend Final Patch

Patched for the latest Profile.js and ReadathonScreen.js.

Added/confirmed:

- Profile fields:
  - parent_name
  - parent_email
  - teacher_name
  - teacher_email
  - auto_parent_reports
  - auto_teacher_reports
  - report_frequency

- Report persistence:
  - ReadathonReport model
  - InterventionNote model
  - serializers with mobile aliases: body, content, report, insight, summary, book_title

- History endpoints:
  - GET /api/readathon/parent-reports/history/
  - GET /api/readathon/teacher-insights/history/
  - GET /api/readathon/interventions/history/

- Save endpoints:
  - POST /api/readathon/parent-reports/save/
  - POST /api/readathon/teacher-insights/save/
  - POST /api/readathon/interventions/save/

- Email endpoints:
  - POST /api/readathon/parent-reports/email/
  - POST /api/readathon/teacher-insights/email/

- Existing endpoints retained:
  - /api/books/
  - /api/my-books/save_progress/
  - /api/readathon/quiz-score/
  - /api/student-scores/
  - /api/ai/chat/
  - /api/game/profile/

Run after extracting:

```cmd
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Email .env example:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=yourgmail@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=yourgmail@gmail.com
```
