from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(10), default="en")
    theme = db.Column(db.String(10), default="light")
    onboarding_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    analyses = db.relationship("Analysis", backref="user", cascade="all, delete-orphan")
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    url = db.Column(db.Text, nullable=False)
    platform = db.Column(db.String(40), nullable=False)
    title = db.Column(db.Text, default="")
    description = db.Column(db.Text, default="")
    media_embed_url = db.Column(db.Text, default="")
    total_comments = db.Column(db.Integer, default=0)
    positive_count = db.Column(db.Integer, default=0)
    negative_count = db.Column(db.Integer, default=0)
    neutral_count = db.Column(db.Integer, default=0)
    sentiment_score = db.Column(db.Float, default=0)
    status = db.Column(db.String(30), default="completed")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    comments = db.relationship("Comment", backref="analysis", cascade="all, delete-orphan")
    recommendations = db.relationship("Recommendation", backref="analysis", cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analysis.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Float, default=0)

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analysis.id"), nullable=False, index=True)
    problem_title = db.Column(db.String(200), nullable=False)
    problem_description = db.Column(db.Text, default="")
    priority = db.Column(db.String(20), default="medium")
    suggested_action = db.Column(db.Text, nullable=False)
    expected_outcome = db.Column(db.Text, default="")
