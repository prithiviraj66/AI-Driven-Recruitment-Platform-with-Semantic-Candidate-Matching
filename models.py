from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='candidate') # 'candidate', 'recruiter', or 'admin'
    is_approved = db.Column(db.Boolean, default=True) # Recruiters require admin approval
    
    # Relationship to Profile
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    company_profile = db.relationship('CompanyProfile', backref='recruiter', uselist=False)
    applications = db.relationship('Application', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    skills = db.Column(db.Text) # Stored as comma-separated values or JSON
    experience = db.Column(db.Text)
    education = db.Column(db.Text)
    resume_path = db.Column(db.String(255))

class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    logo_path = db.Column(db.String(255))
    website = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    description = db.Column(db.Text)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills_required = db.Column(db.Text, nullable=False) # Comma-separated
    location = db.Column(db.String(100))
    salary = db.Column(db.String(50))
    job_type = db.Column(db.String(50), default='Full-time') # Full-time, Internship, etc.
    experience_level = db.Column(db.String(50), default='Entry-level') # Junior, Senior, etc.
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    vacancies = db.Column(db.Integer, default=1, nullable=False)

    @property
    def is_filled(self):
        from models import Application
        filled_count = Application.query.filter(
            Application.job_id == self.id,
            Application.status.in_(['Appointed', 'Selected'])
        ).count()
        return filled_count >= self.vacancies

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    match_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Applied') # 'Applied', 'Interviewing', 'Rejected', etc.
    
    # Relationship to Job
    job = db.relationship('Job', backref='applications', lazy=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

