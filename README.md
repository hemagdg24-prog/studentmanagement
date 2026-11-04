# Student Management & Enrollment System (EduRankAI)

A centralized, responsive, production-ready web application for training organizations to register students, maintain student records, search and filter enrollments, and track live statistics.

Built for the **EduRankAI Full-Stack Engineer Recruitment Assessment**.

---

## 1. Technology Stack

- **Backend:** Python 3.13 / Flask 3.1
- **Database:** PostgreSQL / Supabase PostgreSQL (tested with SQLite for in-memory testing)
- **ORM:** Flask-SQLAlchemy 3.1 (SQLAlchemy 2.x)
- **Database Migrations:** Flask-Migrate 4.1 (Alembic)
- **Frontend:** Jinja2 templates, HTML5, CSS3, JavaScript (ES6)
- **UI Framework:** Bootstrap 5.3.3 & Bootstrap Icons 1.11.3
- **Testing:** Pytest 8.3.4 & pytest-flask
- **Design:** SaaS-style admin portal with custom teal palette, mobile drawer, responsive tables, and confirmation modals

---

## 2. Project Structure

```text
student-management-system/
│
├── app.py                     # Flask application factory, routes, and REST API
├── config.py                  # Configurations (Development, Testing, Production)
├── models.py                  # SQLAlchemy Student model definition
├── extensions.py              # Unbound db and migrate instances
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
├── .env.example               # Template for environment variables
├── .env                       # Local environment variables (git-ignored)
├── .gitignore                 # Standard Python/Flask gitignore
├── README.md                  # Comprehensive setup, run, and API documentation
├── LEARNINGS.md               # Technical decisions, challenges, and solutions
│
├── migrations/                # Flask-Migrate database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── static/
│   ├── css/
│   │   └── style.css          # SaaS admin dashboard theme & responsive layout
│   └── js/
│       └── main.js            # Auto-dismiss alerts, mobile sidebar, auto-submit filters
│
├── templates/
│   ├── base.html              # Responsive layout, sidebar, topbar, and flash alerts
│   ├── dashboard.html         # Real-time statistics cards & 5 recent registrations
│   ├── students.html          # Student records table, search, filters & delete modal
│   ├── add_student.html       # Student registration form with validation
│   ├── edit_student.html      # Update student form pre-populated with current data
│   ├── 404.html               # Custom 404 Not Found error page
│   └── 500.html               # Custom 500 Internal Server Error page
│
└── tests/
    ├── conftest.py            # Pytest fixtures and testing config
    └── test_students.py       # 21 automated unit and integration tests
```

---

## 3. Database Schema

The database uses a PostgreSQL table named `students`:

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY`, Auto-increment | Unique identifier |
| `full_name` | `VARCHAR(150)` | `NOT NULL` | Student full name (2–150 chars) |
| `email` | `VARCHAR(255)` | `NOT NULL`, `UNIQUE`, Indexed | Student email address |
| `phone_number` | `VARCHAR(20)` | `NOT NULL` | Contact number (7–20 digits) |
| `course` | `VARCHAR(150)` | `NOT NULL` | Enrolled course name |
| `enrollment_date`| `DATE` | `NOT NULL` | Date of enrollment (YYYY-MM-DD) |
| `status` | `VARCHAR(10)` | `NOT NULL`, Default: `'Active'` | Either `'Active'` or `'Inactive'` |

---

## 4. Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- PostgreSQL (Local or Supabase / Neon / Railway)
- Git

### Step 1: Clone and Enter the Project
```bash
git clone <repository-url>
cd student-management-system
```

### Step 2: Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Update your `.env` with your PostgreSQL database credentials:
```ini
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secure-secret-key

# Local PostgreSQL example:
DATABASE_URL=postgresql://postgres:password@localhost:5432/student_management

# Or Supabase connection string:
# DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
```

### Step 5: Initialize the Database Schema

If using PostgreSQL with migrations:
```bash
flask db migrate -m "Initial student table"
flask db upgrade
```

Or initialize tables directly via Python shell:
```bash
python -c "from app import create_app; from extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

---

## 5. Running the Application

Start the Flask development server:
```bash
flask run --port=5000 --debug
```
Or:
```bash
python app.py
```

Open your browser at:
```text
http://127.0.0.1:5000/
```

---

## 6. Features & Usage Guide

1. **Dashboard (`/dashboard`)**:
   - Total Students registered.
   - Active Students count.
   - Inactive Students count.
   - 5 most recent registrations table with instant edit actions.
2. **Student Directory (`/students`)**:
   - Tabular view of all registered students with avatar initials, contact, course, date, and status badges.
   - Real-time search by student name or email.
   - Filter dropdown by Course.
   - Filter dropdown by Status (`Active` / `Inactive`).
   - Pagination (10 records per page) preserving active filters.
3. **Add Student (`/students/add`)**:
   - Comprehensive form with field-level validation and required indicators.
   - Prevents duplicate email addresses with feedback alerts.
4. **Edit Student (`/students/<id>/edit`)**:
   - Pre-populates all existing student information.
   - Enforces unique email check (ignoring current student ID).
5. **Delete Student (`/students/<id>/delete`)**:
   - Interactive modal confirmation before deletion.
   - Safe deletion with flash notification.

---

## 7. REST API Documentation

All endpoints return and accept JSON.

### Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard` | Get student aggregate metrics and recent entries |
| `GET` | `/api/students` | Get paginated list of students with query & filter support |
| `POST` | `/api/students` | Create a new student record |
| `GET` | `/api/students/<id>` | Retrieve a single student by ID |
| `PUT` | `/api/students/<id>` | Update student details by ID |
| `DELETE`| `/api/students/<id>` | Delete a student record by ID |

### Example Payloads

#### Create Student (`POST /api/students`)
```json
{
  "full_name": "Sarah Connor",
  "email": "sarah.connor@example.com",
  "phone_number": "+1 555 987 6543",
  "course": "Cybersecurity",
  "enrollment_date": "2026-11-04",
  "status": "Active"
}
```
**Response (`201 Created`):**
```json
{
  "message": "Student created successfully.",
  "student": {
    "id": 1,
    "full_name": "Sarah Connor",
    "email": "sarah.connor@example.com",
    "phone_number": "+1 555 987 6543",
    "course": "Cybersecurity",
    "enrollment_date": "2026-11-04",
    "status": "Active"
  }
}
```

#### Query Students (`GET /api/students?q=sarah&course=Cybersecurity&status=Active&page=1`)
**Response (`200 OK`):**
```json
{
  "students": [...],
  "total": 1,
  "pages": 1,
  "current_page": 1
}
```

---

## 8. Testing Instructions

The test suite contains 21 unit and integration tests covering:
- Successful student creation and retrieval
- Validation rules (missing fields, email format, phone format, invalid status)
- Duplicate email prevention (application & database levels)
- Update and delete operations (including 404 handling)
- Dashboard metrics and counts
- All HTML page routes and redirects

### Running the Test Suite
```bash
pytest
```

For verbose output with test names:
```bash
pytest -v
```
