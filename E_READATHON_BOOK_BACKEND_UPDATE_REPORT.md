# E-Readathon Book Backend Update

This backend has been updated to support real E-Readathon Library uploads and reading progress.

## Added

- `Book` model for actual library books.
- `UserBook` model for each learner's saved reading progress.
- `/api/books/` endpoint for public/published books.
- `/api/my-books/` endpoint for authenticated learner library/progress.
- `/api/my-books/save_progress/` endpoint for reading progress updates.
- Django admin registration for `Book` and `UserBook`.
- Media storage settings:
  - `MEDIA_URL = 'media/'`
  - `MEDIA_ROOT = BASE_DIR / 'media'`
- Development media serving through Django URLs.
- Migration file: `api/migrations/0002_book_userbook.py`
- Seed data now creates sample E-Readathon book records.

## Upload location

When books are uploaded through Django Admin:

- Cover images: `media/books/covers/`
- Book files/PDFs: `media/books/files/`

## Admin flow

1. Open `/admin/`
2. Add a `Book`
3. Upload cover and file
4. Set `is_published=True`
5. The book appears in the E-Readathon Library tab through `/api/books/`

## After extracting

Run:

```cmd
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
```

Test:

```text
http://127.0.0.1:8000/api/books/
http://127.0.0.1:8000/api/my-books/
```
