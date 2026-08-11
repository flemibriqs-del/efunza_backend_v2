#!/bin/bash

# ============================================================
# EFUNZA BACKEND - LOCAL TEST SETUP & RUN SCRIPT
# ============================================================

set -e  # Exit on first error

echo "🚀 Starting Efunza Backend Setup..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================
# 1. CHECK PYTHON & VIRTUAL ENVIRONMENT
# ============================================================

echo -e "${YELLOW}[1/7]${NC} Checking Python installation..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# ============================================================
# 2. INSTALL DEPENDENCIES
# ============================================================

echo -e "${YELLOW}[2/7]${NC} Installing dependencies..."

pip install --upgrade pip setuptools wheel > /dev/null
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# ============================================================
# 3. CREATE .env FILE (if it doesn't exist)
# ============================================================

echo -e "${YELLOW}[3/7]${NC} Checking environment configuration..."

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file with development defaults...${NC}"
    cat > .env << 'EOF'
# Environment
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Database (SQLite for development)
DATABASE_URL=

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173

# OpenAI (optional)
OPENAI_API_KEY=

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# AWS S3 (optional)
USE_S3=False
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# ============================================================
# 4. RUN MIGRATIONS
# ============================================================

echo -e "${YELLOW}[4/7]${NC} Running database migrations..."

python manage.py makemigrations
python manage.py migrate

echo -e "${GREEN}✓ Migrations completed${NC}"

# ============================================================
# 5. CREATE SUPERUSER (optional)
# ============================================================

echo -e "${YELLOW}[5/7]${NC} Setting up superuser..."

python manage.py shell << 'PYTHON_END'
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@efunza.local', 'admin123')
    print("✓ Superuser 'admin' created with password 'admin123'")
else:
    print("✓ Superuser already exists")
PYTHON_END

echo -e "${GREEN}✓ Superuser setup complete${NC}"

# ============================================================
# 6. CREATE TEST DATA
# ============================================================

echo -e "${YELLOW}[6/7]${NC} Creating test data..."

python manage.py shell << 'PYTHON_END'
from api.models import Program, Book, UserBook
from django.contrib.auth.models import User

# Create test program
if not Program.objects.filter(title='Readathon 2024').exists():
    program = Program.objects.create(
        title='Readathon 2024',
        description='Annual reading challenge for students',
        category='Reading',
        price=0,
        is_active=True
    )
    print(f"✓ Created Program: {program.title}")

# Create test book
if not Book.objects.filter(title='Sample Book').exists():
    book = Book.objects.create(
        title='Sample Book',
        author='Test Author',
        description='This is a sample book for testing',
        category='Fiction',
        grade='10',
        language='English',
        program='e-readathon',
        pages=200,
        is_published=True
    )
    print(f"✓ Created Book: {book.title}")

# Create test user with book
admin_user = User.objects.get(username='admin')
if Book.objects.exists():
    book = Book.objects.first()
    if not UserBook.objects.filter(user=admin_user, book=book).exists():
        user_book = UserBook.objects.create(
            user=admin_user,
            book=book,
            progress=0,
            current_page=0
        )
        print(f"✓ Added book to user library")

PYTHON_END

echo -e "${GREEN}✓ Test data created${NC}"

# ============================================================
# 7. COLLECT STATIC FILES
# ============================================================

echo -e "${YELLOW}[7/7]${NC} Collecting static files..."

python manage.py collectstatic --noinput > /dev/null 2>&1 || true

echo -e "${GREEN}✓ Static files collected${NC}"

# ============================================================
# START SERVER
# ============================================================

echo ""
echo -e "${GREEN}=================================================="
echo "✓ SETUP COMPLETE! Starting development server...${NC}"
echo "=================================================="
echo ""
echo -e "${YELLOW}Access the application at:${NC}"
echo "  API: http://localhost:8000/api/"
echo "  Admin: http://localhost:8000/admin/"
echo "  API Docs: http://localhost:8000/api/schema/"
echo ""
echo -e "${YELLOW}Test Credentials:${NC}"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo -e "${YELLOW}Key Endpoints to Test:${NC}"
echo "  GET  /api/auth/me/ - Current user"
echo "  POST /api/auth/login/ - Login"
echo "  GET  /api/books/ - List books"
echo "  GET  /api/programs/ - List programs"
echo "  POST /api/my-books/ - Add book to library"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start development server
python manage.py runserver 0.0.0.0:8000
