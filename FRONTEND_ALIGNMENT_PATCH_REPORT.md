# Efunza Backend Frontend-Alignment Patch

This backend package was patched to align with the generated Efunza frontend.

## Confirmed/Added

- `user_type` support remains active and now accepts: `student`, `teacher`, `parent`, `mentor`, `school_admin`, `admin`.
- Registration accepts both `user_type` and frontend-style `userType`.
- Profile update accepts both `user_type` and `userType`.
- `Program.slug` and `Program.metadata` added.
- `ProgramViewSet` supports:
  - `GET /api/programs/`
  - `GET /api/programs/by-slug/<slug>/`
  - `POST /api/programs/enroll_by_slug/`
  - `POST /api/programs/<id>/enroll/`
- `EnrollmentViewSet` supports:
  - `POST /api/enrollments/enroll_by_slug/`
  - `POST /api/enrollments/efunza/`
  - `GET /api/enrollments/check_status/?email=...`
- Added frontend-aligned resource endpoints:
  - `/api/books/`
  - `/api/my-books/`
  - `/api/achievements/`
  - `/api/notifications/`
  - `/api/subscriptions/`
  - `/api/lab-projects/`
- Added gamification endpoints:
  - `/api/game/profile/`
  - `/api/game/leaderboard/`
- Seed command now creates all 15 Efunza programs with E²IO metadata, AI feature, gamification, intelligence layer, labs, and career pathways.
- Added `api/migrations/0001_initial.py` so fresh installs can migrate without needing to generate migrations manually.

## Commands

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
```

## Notes

M-Pesa and AI chat remain placeholder-safe and should be connected to live providers before real production billing or AI use.
