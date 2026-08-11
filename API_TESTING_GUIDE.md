# 🧪 Efunza Backend - API Testing Guide

**Status:** ✅ Ready to Test  
**Date:** 2026-08-09  
**Backend Version:** Aligned with Frontend

---

## 🚀 Quick Start

### Step 1: Run the Local Test Server

```bash
# Clone the repo (if not already done)
git clone https://github.com/efunza/backend_1.git
cd backend_1

# Run the automated setup script
bash run_local_test.sh
```

This will:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Set up database (SQLite)
- ✅ Run migrations
- ✅ Create test data
- ✅ Start the server on `http://localhost:8000`

### Step 2: Access the Application

| Resource | URL | Notes |
|----------|-----|-------|
| **API Root** | `http://localhost:8000/api/` | Browse all endpoints |
| **Admin Panel** | `http://localhost:8000/admin/` | Manage data |
| **Admin Credentials** | `admin` / `admin123` | Auto-created |
| **API Docs** | `http://localhost:8000/api/schema/` | OpenAPI schema |

---

## 📝 Testing with cURL or Postman

### 1️⃣ Authentication

#### Login (Get JWT Token)
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@efunza.local",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@efunza.local",
    "first_name": "",
    "last_name": "",
    "name": "admin",
    "profile": {...}
  }
}
```

**Save the access token for subsequent requests:**
```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

#### Get Current User
```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2️⃣ Books & Readathon

#### List All Books
```bash
curl -X GET http://localhost:8000/api/books/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Sample Book",
      "slug": "sample-book",
      "author": "Test Author",
      "description": "This is a sample book for testing",
      "category": "Fiction",
      "grade": "10",
      "language": "English",
      "program": "e-readathon",
      "cover": null,
      "cover_url": "",
      "file": null,
      "file_url": "",
      "pdf": null,
      "pdf_url": "",
      "external_url": "",
      "pages": 200,
      "estimated_minutes": 0,
      "xp_reward": 50,
      "is_featured": false,
      "is_published": true,
      "created_at": "2026-08-09T16:19:30.123456Z",
      "updated_at": "2026-08-09T16:19:30.123456Z"
    }
  ]
}
```

**✅ Note:** `pdf_url` field is now present (the fix we applied!)

#### Get User's Books (My Library)
```bash
curl -X GET http://localhost:8000/api/my-books/ \
  -H "Authorization: Bearer $TOKEN"
```

#### Add Book to User's Library
```bash
curl -X POST http://localhost:8000/api/my-books/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "book": 1,
    "progress": 0,
    "current_page": 0
  }'
```

#### Update Reading Progress
```bash
curl -X PATCH http://localhost:8000/api/my-books/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "progress": 45.5,
    "current_page": 90,
    "reading_minutes": 120,
    "last_read_at": "2026-08-09T16:19:30Z"
  }'
```

---

### 3️⃣ Programs & Enrollment

#### List Programs
```bash
curl -X GET http://localhost:8000/api/programs/ \
  -H "Authorization: Bearer $TOKEN"
```

#### Enroll in Program
```bash
curl -X POST http://localhost:8000/api/enrollments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "program": 1,
    "status": "active"
  }'
```

---

### 4️⃣ E-Lab Projects

#### List E-Lab Projects
```bash
curl -X GET http://localhost:8000/api/elab-projects/ \
  -H "Authorization: Bearer $TOKEN"
```

#### Create New Project
```bash
curl -X POST http://localhost:8000/api/elab-projects/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "My First Lab Project",
    "description": "Testing E-Lab integration",
    "status": "draft"
  }'
```

---

### 5️⃣ Maritime Academy

#### List Maritime Courses
```bash
curl -X GET http://localhost:8000/api/maritime-courses/ \
  -H "Authorization: Bearer $TOKEN"
```

#### Enroll in Maritime Course
```bash
curl -X POST http://localhost:8000/api/maritime-enrollments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "course_id": 1,
    "track": "university"
  }'
```

---

### 6️⃣ User Profile

#### Get Profile
```bash
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer $TOKEN"
```

#### Update Profile
```bash
curl -X PATCH http://localhost:8000/api/profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "phone": "254712345678",
    "school": "Nairobi High School",
    "county": "Nairobi",
    "grade": "Grade 10",
    "career_interest": "Software Engineering"
  }'
```

---

## 🔍 Testing Checklist

### Backend Alignment Tests ✅

- [ ] **Book PDF URL**
  - Test: `GET /api/books/1/`
  - Check: `pdf_url` field present in response
  - Expected: Empty string or full URL to PDF

- [ ] **Authentication**
  - Test: `POST /api/auth/login/`
  - Check: Returns `access`, `refresh`, `user` tokens
  - Expected: JWT tokens valid

- [ ] **Readathon Reading Progress**
  - Test: `PATCH /api/my-books/1/`
  - Check: Progress, current_page, reading_minutes update
  - Expected: 200 OK with updated data

- [ ] **E-Lab Projects**
  - Test: `GET /api/elab-projects/`
  - Check: Endpoint returns list of projects
  - Expected: 200 OK with results array

- [ ] **Maritime Academy**
  - Test: `GET /api/maritime-courses/`
  - Check: Endpoint returns courses with track field
  - Expected: 200 OK with results array

- [ ] **CORS Headers**
  - Test: Make request from `http://localhost:3000` or `http://localhost:5173`
  - Check: Response includes `Access-Control-Allow-Origin` header
  - Expected: `Access-Control-Allow-Origin: http://localhost:3000`

---

## 📦 Using Postman

### Import Collection

1. Open Postman
2. Click **Import**
3. Paste this URL or create manually from examples above
4. Set base URL: `http://localhost:8000/api`

### Environment Variables

Set in Postman:
```
BASE_URL: http://localhost:8000/api
TOKEN: (paste token from login response)
```

### Example Requests

**Login**
- Method: `POST`
- URL: `{{BASE_URL}}/auth/login/`
- Body (JSON):
  ```json
  {
    "email": "admin@efunza.local",
    "password": "admin123"
  }
  ```

**Get Books**
- Method: `GET`
- URL: `{{BASE_URL}}/books/`
- Headers:
  - `Authorization: Bearer {{TOKEN}}`

---

## 🐛 Troubleshooting

### Error: "Port 8000 already in use"
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python manage.py runserver 0.0.0.0:8001
```

### Error: "ModuleNotFoundError: No module named 'api'"
```bash
# Make sure you're in the project root
cd backend_1

# Activate virtual environment
source venv/bin/activate

# Run again
python manage.py runserver
```

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"
- Verify frontend domain is in `CORS_ALLOWED_ORIGINS` in `settings.py`
- For local testing, `http://localhost:3000` and `http://localhost:5173` are pre-configured

### Error: "Authentication credentials were not provided"
- Make sure you're including the Authorization header
- Use the access token from login response
- Format: `Authorization: Bearer <token>`

---

## 📊 Expected Response Examples

### Books with PDF URL
```json
{
  "id": 1,
  "title": "Sample Book",
  "pdf": "books/pdfs/sample.pdf",
  "pdf_url": "http://localhost:8000/media/books/pdfs/sample.pdf",
  "file_url": "http://localhost:8000/media/books/files/sample.pdf",
  "cover_url": "http://localhost:8000/media/books/covers/cover.jpg"
}
```

### User Profile
```json
{
  "user_type": "student",
  "phone": "254712345678",
  "school": "Nairobi High School",
  "county": "Nairobi",
  "grade": "Grade 10",
  "career_interest": "Software Engineering",
  "parent_name": "John Doe",
  "parent_email": "parent@example.com",
  "teacher_name": "Jane Smith",
  "teacher_email": "teacher@example.com",
  "auto_parent_reports": true,
  "auto_teacher_reports": true,
  "report_frequency": "weekly"
}
```

---

## 🎯 Next Steps

1. **✅ Run Setup Script**
   ```bash
   bash run_local_test.sh
   ```

2. **✅ Test Endpoints**
   - Use the cURL commands above or Postman
   - Verify all key endpoints work

3. **✅ Test with Frontend**
   - Run frontend on `http://localhost:3000` or `http://localhost:5173`
   - Verify API responses match frontend expectations

4. **✅ Deploy to Production**
   - Update `ALLOWED_HOSTS` in settings
   - Update `CORS_ALLOWED_ORIGINS` with production domain
   - Set `DEBUG=False`
   - Use proper database (PostgreSQL recommended)

---

## 📞 Support

If you encounter issues:

1. Check logs: `tail -f logs/errors.log`
2. Review Django shell: `python manage.py shell`
3. Test database: `python manage.py dbshell`
4. Verify migrations: `python manage.py showmigrations`

---

**Last Updated:** 2026-08-09  
**Status:** ✅ Ready for Testing
