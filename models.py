from datetime import date
from extensions import db


class Student(db.Model):
    """Student model representing the students table in PostgreSQL."""

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    phone_number = db.Column(db.String(20), nullable=False)
    course = db.Column(db.String(150), nullable=False)
    enrollment_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(
        db.String(10),
        nullable=False,
        default="Active",
        server_default="Active",
    )

    def __repr__(self):
        return f"<Student {self.id}: {self.full_name}>"

    def to_dict(self):
        """Serialise the model to a JSON-safe dict."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "course": self.course,
            "enrollment_date": self.enrollment_date.isoformat() if self.enrollment_date else None,
            "status": self.status,
        }

