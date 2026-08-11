# E-Readathon Reports/Email/Interventions Patch

Added backend support for:

- Parent report history: `/api/readathon/reports/`
- Teacher insight history: `/api/readathon/reports/` with `report_type=teacher`
- Email sending: `/api/readathon/reports/<id>/send_email/`
- Intervention notes: `/api/readathon/interventions/`
- Console email backend for local testing

Run:

```cmd
python manage.py migrate
```

For real email delivery, configure SMTP settings and DEFAULT_FROM_EMAIL in production.
