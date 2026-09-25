"""
Database Models - ReqCraft AI
Uses Flask-SQLAlchemy + SQLite (zero-cost local DB).
"""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship("SRSDocument", backref="user", lazy=True,
                                cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class SRSDocument(db.Model):
    __tablename__ = "srs_documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    project_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)               # generated SRS markdown
    source = db.Column(db.String(20), default="generated")  # generated | uploaded

    provider = db.Column(db.String(40))        # which LLM produced it
    compliance_score = db.Column(db.Integer, default=0)
    quality_score = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_name": self.project_name,
            "source": self.source,
            "provider": self.provider,
            "compliance_score": self.compliance_score,
            "quality_score": self.quality_score,
            "created_at": self.created_at.strftime("%d %b %Y, %H:%M") if self.created_at else "",
        }
