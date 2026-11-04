"""
app.py — Application factory and route definitions.
Student Management & Enrollment System
"""
import re
from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from config import config
from extensions import db, migrate
from models import Student


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints / routes
    register_routes(app)

    return app


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^\+?[\d\s\-().]{7,20}$")

AVAILABLE_COURSES = [
    "Data Science",
    "Web Development",
    "Mobile Development",
    "Cloud Computing",
    "Cybersecurity",
    "Machine Learning",
    "DevOps Engineering",
    "UI/UX Design",
    "Blockchain Development",
    "Digital Marketing",
]


def validate_student_data(data: dict, is_update: bool = False) -> list[str]:
    """Return a list of validation error strings (empty = valid)."""
    errors = []

    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()
    phone_number = data.get("phone_number", "").strip()
    course = data.get("course", "").strip()
    enrollment_date = data.get("enrollment_date", "").strip()
    status = data.get("status", "").strip()

    if not full_name:
        errors.append("Full name is required.")
    elif len(full_name) < 2:
        errors.append("Full name must be at least 2 characters.")
    elif len(full_name) > 150:
        errors.append("Full name must not exceed 150 characters.")

    if not email:
        errors.append("Email address is required.")
    elif not EMAIL_RE.match(email):
        errors.append("Please enter a valid email address.")

    if not phone_number:
        errors.append("Phone number is required.")
    elif not PHONE_RE.match(phone_number):
        errors.append("Please enter a valid phone number (7–20 digits, may include +, -, spaces).")

    if not course:
        errors.append("Course is required.")

    if not enrollment_date:
        errors.append("Enrollment date is required.")
    else:
        try:
            datetime.strptime(enrollment_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Enrollment date must be in YYYY-MM-DD format.")

    if status not in ("Active", "Inactive"):
        errors.append("Status must be 'Active' or 'Inactive'.")

    return errors


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

def register_routes(app: Flask) -> None:

    # -----------------------------------------------------------------------
    # Page routes (HTML)
    # -----------------------------------------------------------------------

    @app.route("/")
    def index():
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    def dashboard():
        total = db.session.query(func.count(Student.id)).scalar() or 0
        active = db.session.query(func.count(Student.id)).filter_by(status="Active").scalar() or 0
        inactive = db.session.query(func.count(Student.id)).filter_by(status="Inactive").scalar() or 0
        recent = (
            Student.query
            .order_by(Student.enrollment_date.desc(), Student.id.desc())
            .limit(5)
            .all()
        )
        return render_template(
            "dashboard.html",
            total=total,
            active=active,
            inactive=inactive,
            recent=recent,
        )

    @app.route("/students")
    def students():
        query = request.args.get("q", "").strip()
        course_filter = request.args.get("course", "").strip()
        status_filter = request.args.get("status", "").strip()
        page = request.args.get("page", 1, type=int)

        stmt = Student.query

        if query:
            like = f"%{query}%"
            stmt = stmt.filter(
                Student.full_name.ilike(like) | Student.email.ilike(like)
            )

        if course_filter:
            stmt = stmt.filter(Student.course == course_filter)

        if status_filter in ("Active", "Inactive"):
            stmt = stmt.filter(Student.status == status_filter)

        pagination = stmt.order_by(Student.id.desc()).paginate(page=page, per_page=10, error_out=False)

        return render_template(
            "students.html",
            students=pagination.items,
            pagination=pagination,
            query=query,
            course_filter=course_filter,
            status_filter=status_filter,
            courses=AVAILABLE_COURSES,
        )

    @app.route("/students/add", methods=["GET", "POST"])
    def add_student():
        if request.method == "POST":
            data = request.form.to_dict()
            errors = validate_student_data(data)

            if errors:
                for error in errors:
                    flash(error, "danger")
                return render_template("add_student.html", courses=AVAILABLE_COURSES, form_data=data)

            # Check duplicate email at app level for a friendlier message
            existing = Student.query.filter_by(email=data["email"].strip().lower()).first()
            if existing:
                flash(f"A student with email '{data['email']}' already exists.", "danger")
                return render_template("add_student.html", courses=AVAILABLE_COURSES, form_data=data)

            try:
                student = Student(
                    full_name=data["full_name"].strip(),
                    email=data["email"].strip().lower(),
                    phone_number=data["phone_number"].strip(),
                    course=data["course"].strip(),
                    enrollment_date=datetime.strptime(data["enrollment_date"], "%Y-%m-%d").date(),
                    status=data["status"],
                )
                db.session.add(student)
                db.session.commit()
                flash(f"Student '{student.full_name}' has been registered successfully!", "success")
                return redirect(url_for("students"))
            except IntegrityError:
                db.session.rollback()
                flash("A student with that email already exists.", "danger")
                return render_template("add_student.html", courses=AVAILABLE_COURSES, form_data=data)
            except Exception as e:
                db.session.rollback()
                flash(f"An unexpected error occurred: {str(e)}", "danger")
                return render_template("add_student.html", courses=AVAILABLE_COURSES, form_data=data)

        return render_template(
            "add_student.html",
            courses=AVAILABLE_COURSES,
            form_data={},
            today=date.today().isoformat(),
        )

    @app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
    def edit_student(student_id):
        student = db.session.get(Student, student_id) or abort(404)

        if request.method == "POST":
            data = request.form.to_dict()
            errors = validate_student_data(data, is_update=True)

            if errors:
                for error in errors:
                    flash(error, "danger")
                return render_template("edit_student.html", student=student, courses=AVAILABLE_COURSES, form_data=data)

            # Check for duplicate email (excluding the current student)
            new_email = data["email"].strip().lower()
            existing = Student.query.filter(
                Student.email == new_email,
                Student.id != student_id
            ).first()
            if existing:
                flash(f"Another student already uses the email '{data['email']}'.", "danger")
                return render_template("edit_student.html", student=student, courses=AVAILABLE_COURSES, form_data=data)

            try:
                student.full_name = data["full_name"].strip()
                student.email = new_email
                student.phone_number = data["phone_number"].strip()
                student.course = data["course"].strip()
                student.enrollment_date = datetime.strptime(data["enrollment_date"], "%Y-%m-%d").date()
                student.status = data["status"]
                db.session.commit()
                flash(f"Student '{student.full_name}' updated successfully!", "success")
                return redirect(url_for("students"))
            except IntegrityError:
                db.session.rollback()
                flash("That email is already in use by another student.", "danger")
                return render_template("edit_student.html", student=student, courses=AVAILABLE_COURSES, form_data=data)
            except Exception as e:
                db.session.rollback()
                flash(f"An unexpected error occurred: {str(e)}", "danger")
                return render_template("edit_student.html", student=student, courses=AVAILABLE_COURSES, form_data=data)

        form_data = {
            "full_name": student.full_name,
            "email": student.email,
            "phone_number": student.phone_number,
            "course": student.course,
            "enrollment_date": student.enrollment_date.isoformat() if student.enrollment_date else "",
            "status": student.status,
        }
        return render_template("edit_student.html", student=student, courses=AVAILABLE_COURSES, form_data=form_data)

    @app.route("/students/<int:student_id>/delete", methods=["POST"])
    def delete_student(student_id):
        student = db.session.get(Student, student_id) or abort(404)
        name = student.full_name
        try:
            db.session.delete(student)
            db.session.commit()
            flash(f"Student '{name}' has been deleted.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Could not delete student: {str(e)}", "danger")
        return redirect(url_for("students"))

    # -----------------------------------------------------------------------
    # REST API endpoints (JSON)
    # -----------------------------------------------------------------------

    @app.route("/api/dashboard", methods=["GET"])
    def api_dashboard():
        total = db.session.query(func.count(Student.id)).scalar() or 0
        active = db.session.query(func.count(Student.id)).filter_by(status="Active").scalar() or 0
        inactive = db.session.query(func.count(Student.id)).filter_by(status="Inactive").scalar() or 0
        recent = (
            Student.query
            .order_by(Student.enrollment_date.desc(), Student.id.desc())
            .limit(5)
            .all()
        )
        return jsonify({
            "total_students": total,
            "active_students": active,
            "inactive_students": inactive,
            "recent_registrations": [s.to_dict() for s in recent],
        })

    @app.route("/api/students", methods=["GET"])
    def api_get_students():
        query = request.args.get("q", "").strip()
        course_filter = request.args.get("course", "").strip()
        status_filter = request.args.get("status", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        stmt = Student.query

        if query:
            like = f"%{query}%"
            stmt = stmt.filter(
                Student.full_name.ilike(like) | Student.email.ilike(like)
            )
        if course_filter:
            stmt = stmt.filter(Student.course == course_filter)
        if status_filter in ("Active", "Inactive"):
            stmt = stmt.filter(Student.status == status_filter)

        pagination = stmt.order_by(Student.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            "students": [s.to_dict() for s in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
        })

    @app.route("/api/students", methods=["POST"])
    def api_create_student():
        data = request.get_json(force=True, silent=True) or {}

        # Normalise date field
        form_like = {k: (str(v).strip() if v is not None else "") for k, v in data.items()}
        errors = validate_student_data(form_like)

        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 422

        existing = Student.query.filter_by(email=form_like["email"].lower()).first()
        if existing:
            return jsonify({"error": "A student with that email already exists."}), 409

        try:
            student = Student(
                full_name=form_like["full_name"],
                email=form_like["email"].lower(),
                phone_number=form_like["phone_number"],
                course=form_like["course"],
                enrollment_date=datetime.strptime(form_like["enrollment_date"], "%Y-%m-%d").date(),
                status=form_like["status"],
            )
            db.session.add(student)
            db.session.commit()
            return jsonify({"message": "Student created successfully.", "student": student.to_dict()}), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "A student with that email already exists."}), 409
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/students/<int:student_id>", methods=["GET"])
    def api_get_student(student_id):
        student = db.session.get(Student, student_id) or abort(404)
        return jsonify(student.to_dict())

    @app.route("/api/students/<int:student_id>", methods=["PUT"])
    def api_update_student(student_id):
        student = db.session.get(Student, student_id) or abort(404)
        data = request.get_json(force=True, silent=True) or {}
        form_like = {k: (str(v).strip() if v is not None else "") for k, v in data.items()}
        errors = validate_student_data(form_like, is_update=True)

        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 422

        new_email = form_like["email"].lower()
        existing = Student.query.filter(Student.email == new_email, Student.id != student_id).first()
        if existing:
            return jsonify({"error": "Another student already uses that email."}), 409

        try:
            student.full_name = form_like["full_name"]
            student.email = new_email
            student.phone_number = form_like["phone_number"]
            student.course = form_like["course"]
            student.enrollment_date = datetime.strptime(form_like["enrollment_date"], "%Y-%m-%d").date()
            student.status = form_like["status"]
            db.session.commit()
            return jsonify({"message": "Student updated successfully.", "student": student.to_dict()})
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "That email is already in use."}), 409
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/students/<int:student_id>", methods=["DELETE"])
    def api_delete_student(student_id):
        student = db.session.get(Student, student_id) or abort(404)
        try:
            db.session.delete(student)
            db.session.commit()
            return jsonify({"message": f"Student '{student.full_name}' deleted successfully."})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    # -----------------------------------------------------------------------
    # Error handlers
    # -----------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found."}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error."}), 500
        return render_template("500.html"), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

