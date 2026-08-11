# Backend ↔ Frontend Alignment Report

This backend was checked against the full frontend package `efunza_full_src_ereadathon_elab_consistent.zip`.

## Confirmed aligned
- `/api/auth/register/`
- `/api/auth/login/`
- `/api/token/` now accepts email/password and returns JWT-compatible payload
- `/api/token/refresh/`
- `/api/token/verify/`
- `/api/me/`
- `/api/programs/`
- `/api/programs/enroll_by_slug/`
- `/api/enrollments/`
- `/api/enrollments/efunza/`
- `/api/books/`
- `/api/my-books/`
- `/api/achievements/`
- `/api/notifications/`
- `/api/subscriptions/`
- `/api/lab-projects/`
- `/api/game/profile/` now supports GET, POST, PATCH
- `/api/game/leaderboard/`
- `/api/student-intelligence/`
- `/api/e2io/`
- `/api/ai/chat/`
- `/api/mpesa/initiate/`
- `/api/mpesa/status/<order_number>/`

## Added compatibility aliases
Added lightweight active endpoints for legacy frontend modules:
- analytics dashboard endpoints
- environmental/green endpoints
- partner/project endpoints
- certificate/blockchain placeholder endpoints
- student creation placeholder endpoint

These return safe placeholder JSON instead of 404, so old screens do not hard-fail while you build full implementations.

## Important
Run:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
```
