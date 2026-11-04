"""
tests/test_students.py
Pytest test suite for the Student Management & Enrollment System.
Day 1: Basic structure — will be expanded in Day 3.
"""
import os
import pytest
from datetime import date

# Default test DB to in-memory SQLite if TEST_DATABASE_URL is not set
if "TEST_DATABASE_URL" not in os.environ:
    os.environ["TEST_DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from extensions import db
from models import Student


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Create application configured for testing."""
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture(scope="function", autouse=True)
def clean_db(app):
    """Wipe the students table before each test."""
    with app.app_context():
        db.session.query(Student).delete()
        db.session.commit()
    yield


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_payload():
    return {
        "full_name": "Alice Johnson",
        "email": "alice@example.com",
        "phone_number": "+1 555 123 4567",
        "course": "Data Science",
        "enrollment_date": str(date.today()),
        "status": "Active",
    }


# ---------------------------------------------------------------------------
# API: Create Student — POST /api/students
# ---------------------------------------------------------------------------

class TestCreateStudent:
    def test_create_student_success(self, client, sample_payload):
        """Successfully create a student via the API."""
        resp = client.post("/api/students", json=sample_payload)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["student"]["email"] == sample_payload["email"].lower()
        assert data["student"]["full_name"] == sample_payload["full_name"]

    def test_create_student_missing_name(self, client, sample_payload):
        """Missing full_name should return 422."""
        sample_payload.pop("full_name")
        resp = client.post("/api/students", json=sample_payload)
        assert resp.status_code == 422

    def test_create_student_invalid_email(self, client, sample_payload):
        """Invalid email should return 422."""
        sample_payload["email"] = "not-an-email"
        resp = client.post("/api/students", json=sample_payload)
        assert resp.status_code == 422

    def test_create_student_duplicate_email(self, client, sample_payload):
        """Duplicate email should return 409."""
        client.post("/api/students", json=sample_payload)
        resp = client.post("/api/students", json=sample_payload)
        assert resp.status_code == 409

    def test_create_student_invalid_status(self, client, sample_payload):
        """Invalid status value should return 422."""
        sample_payload["status"] = "Maybe"
        resp = client.post("/api/students", json=sample_payload)
        assert resp.status_code == 422

    def test_create_student_invalid_phone(self, client, sample_payload):
        """Too-short phone number should fail validation."""
        sample_payload["phone_number"] = "123"
        resp = client.post("/api/students", json=sample_payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# API: Get Students — GET /api/students
# ---------------------------------------------------------------------------

class TestGetStudents:
    def test_get_students_empty(self, client):
        """Empty table should return an empty list."""
        resp = client.get("/api/students")
        assert resp.status_code == 200
        assert resp.get_json()["students"] == []

    def test_get_students_returns_all(self, client, sample_payload):
        """Seeded student should appear in the list."""
        client.post("/api/students", json=sample_payload)
        resp = client.get("/api/students")
        data = resp.get_json()
        assert data["total"] == 1
        assert data["students"][0]["email"] == sample_payload["email"].lower()

    def test_get_student_by_id(self, client, sample_payload):
        """GET /api/students/<id> should return the correct student."""
        create_resp = client.post("/api/students", json=sample_payload)
        student_id = create_resp.get_json()["student"]["id"]
        resp = client.get(f"/api/students/{student_id}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == student_id

    def test_get_nonexistent_student(self, client):
        """GET for a non-existent ID should return 404."""
        resp = client.get("/api/students/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# API: Update Student — PUT /api/students/<id>
# ---------------------------------------------------------------------------

class TestUpdateStudent:
    def test_update_student_success(self, client, sample_payload):
        """Successfully update a student's course."""
        create_resp = client.post("/api/students", json=sample_payload)
        student_id = create_resp.get_json()["student"]["id"]
        updated = {**sample_payload, "course": "Cloud Computing"}
        resp = client.put(f"/api/students/{student_id}", json=updated)
        assert resp.status_code == 200
        assert resp.get_json()["student"]["course"] == "Cloud Computing"

    def test_update_student_duplicate_email(self, client, sample_payload):
        """Updating to another student's email should return 409."""
        client.post("/api/students", json=sample_payload)
        second = {**sample_payload, "email": "bob@example.com"}
        create_resp = client.post("/api/students", json=second)
        student_id = create_resp.get_json()["student"]["id"]
        updated = {**second, "email": sample_payload["email"]}
        resp = client.put(f"/api/students/{student_id}", json=updated)
        assert resp.status_code == 409

    def test_update_nonexistent_student(self, client, sample_payload):
        """Updating a non-existent student should return 404."""
        resp = client.put("/api/students/99999", json=sample_payload)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# API: Delete Student — DELETE /api/students/<id>
# ---------------------------------------------------------------------------

class TestDeleteStudent:
    def test_delete_student_success(self, client, sample_payload):
        """Successfully delete a student."""
        create_resp = client.post("/api/students", json=sample_payload)
        student_id = create_resp.get_json()["student"]["id"]
        resp = client.delete(f"/api/students/{student_id}")
        assert resp.status_code == 200
        # Verify it's gone
        get_resp = client.get(f"/api/students/{student_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_student(self, client):
        """Deleting a non-existent student should return 404."""
        resp = client.delete("/api/students/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# API: Dashboard — GET /api/dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_dashboard_empty(self, client):
        """Dashboard stats should be zero when no students exist."""
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_students"] == 0
        assert data["active_students"] == 0
        assert data["inactive_students"] == 0

    def test_dashboard_counts(self, client, sample_payload):
        """Dashboard counts should reflect actual DB state."""
        client.post("/api/students", json=sample_payload)
        inactive = {**sample_payload, "email": "bob@example.com", "status": "Inactive"}
        client.post("/api/students", json=inactive)
        resp = client.get("/api/dashboard")
        data = resp.get_json()
        assert data["total_students"] == 2
        assert data["active_students"] == 1
        assert data["inactive_students"] == 1


# ---------------------------------------------------------------------------
# Page Routes (HTML)
# ---------------------------------------------------------------------------

class TestPageRoutes:
    def test_dashboard_page(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert b"EduRank" in resp.data

    def test_students_page(self, client):
        resp = client.get("/students")
        assert resp.status_code == 200

    def test_add_student_page(self, client):
        resp = client.get("/students/add")
        assert resp.status_code == 200

    def test_root_redirects_to_dashboard(self, client):
        resp = client.get("/")
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

