# Efunza Backend API

Django REST backend aligned to the Efunza mobile/frontend API service.

## Quick start
```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux/Mac
pip install -r requirements.txt
copy .env.example .env     # Windows
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Base URL: `http://127.0.0.1:8000/api`

## Main endpoints
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/token/refresh/`
- `GET/PATCH /api/me/`
- `GET/PATCH /api/auth/privacy-settings/`
- CRUD resources: `/api/tasks/`, `/api/notes/`, `/api/discussions/`, `/api/assignments/`, `/api/grades/`, `/api/events/`, `/api/study-groups/`, `/api/career-sessions/`
- Learning: `/api/programs/`, `/api/lessons/`, `/api/videos/`, `/api/content/`, `/api/assessments/`, `/api/student-scores/`
- Intelligence: `/api/student-intelligence/summary/`, `/api/student-intelligence/profiles/`, `/api/e2io/maturity/`
- Support: `/api/feedback/`, `/api/support/contact/`
- AI: `/api/ai/chat/`
- M-Pesa placeholder: `/api/mpesa/initiate/`, `/api/mpesa/status/<order_number>/`

Set your React Native `BASE_URL` to the deployed `/api` path.
"# efunza_backend_v2" 
