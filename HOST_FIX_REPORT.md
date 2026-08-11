# Host Fix Report

## Problem found
Django was still rejecting requests from `192.168.188.7:8000` with `DisallowedHost`.

## Root cause
The backend relied on `ALLOWED_HOSTS` from `.env`. If the running environment did not load the expected `.env`, or if a different extracted backend copy was used, Django rejected LAN/mobile requests.

## Fix applied
`settings.py` now includes a robust local testing override:

```python
LOCAL_ALLOW_ALL_HOSTS = config('LOCAL_ALLOW_ALL_HOSTS', default=True, cast=bool)

if DEBUG and LOCAL_ALLOW_ALL_HOSTS:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = config(...)
```

`.env` now includes:

```env
LOCAL_ALLOW_ALL_HOSTS=True
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.188.7,kupalia21.pythonanywhere.com,www.kupalia21.pythonanywhere.com
```

## Important security note
The exposed OpenAI key was removed from the packaged `.env`. Add a newly rotated key locally.

## After extracting
Run:

```cmd
python manage.py runserver 0.0.0.0:8000
```

Then test:

```text
http://192.168.188.7:8000/api/programs/
```
