# Efunza Backend AI E-Lab Complete Update

This backend has been upgraded while preserving your existing backend files.

Added inside app folder:

```txt
api/elab_ai_models.py
api/elab_ai_serializers.py
api/elab_ai_views.py
api/elab_ai_urls.py
api/ai_engine.py
```

## New endpoints

```txt
/api/ai/chat/
/api/ai/student-insight/
/api/elab-projects/
/api/elab-projects/{id}/ai_coach/
/api/elab-projects/{id}/score_innovation/
/api/ai-elab/health/
```

Depending on your existing URL structure, these may be mounted under your app's existing `/api/` include.

## After copying

Run:

```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## AI

Set in `.env`:

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

Without a key, it works in demo mode.
