from main import app, db, bcrypt
from models import Job, User, UserProfile
import random

def seed_jobs():
    jobs_data = [
        {
            "title": "Senior Python Developer",
            "company": "TechNova Solutions",
            "description": "We are looking for a Python expert to lead our backend team in building scalable cloud services. You will work with Flask, AWS, and Docker.",
            "skills_required": "python, flask, aws, docker, sql",
            "location": "San Francisco, CA",
            "salary": "$140,000 - $180,000"
        },
        {
            "title": "Frontend Engineer (React)",
            "company": "DesignSphere",
            "description": "Join our creative team to build stunning user interfaces. Must be proficient in React, CSS, and modern web design principles.",
            "skills_required": "javascript, react, html, css, tailwind",
            "location": "Remote",
            "salary": "$110,000 - $150,000"
        },
        {
            "title": "Data Scientist",
            "company": "Insight Analytics",
            "description": "Analyze large datasets and build predictive models using machine learning. Experience with Pandas, Scikit-learn, and NLP is required.",
            "skills_required": "python, pandas, scikit-learn, nlp, sql, machine learning",
            "location": "New York, NY",
            "salary": "$130,000 - $170,000"
        },
        {
            "title": "DevOps Engineer",
            "company": "CloudScale",
            "description": "Automate our infrastructure and optimize deployment pipelines using Kubernetes and Terraform.",
            "skills_required": "aws, linux, kubernetes, docker, git, terraform",
            "location": "Austin, TX",
            "salary": "$125,000 - $165,000"
        },
        {
            "title": "Full Stack Developer",
            "company": "Startup Hub",
            "description": "A versatile developer who can handle both front-end (React) and back-end (Django/Node).",
            "skills_required": "python, javascript, django, node.js, react, mongodb",
            "location": "Seattle, WA",
            "salary": "$115,000 - $155,000"
        },
        {
            "title": "ML Engineer",
            "company": "AIVision",
            "description": "Build high-performance deep learning models for computer vision and speech recognition.",
            "skills_required": "python, deep learning, pytorch, tensorflow, linux",
            "location": "Boston, MA",
            "salary": "$150,000 - $200,000"
        },
        {
            "title": "Product Designer",
            "company": "UserFirst",
            "description": "Design user-centric products and conduct UX research.",
            "skills_required": "ui/ux, figma, design thinking, html",
            "location": "Remote",
            "salary": "$90,000 - $130,000"
        }
    ]

    with app.app_context():
        # Ensure tables exist
        db.create_all()
        # Clear existing jobs if any
        # db.session.query(Job).delete()
        
        for job_info in jobs_data:
            job = Job(**job_info)
            db.session.add(job)
        
        # Add an Admin User
        admin_email = "admin@jobrecommend.com"
        if not User.query.filter_by(email=admin_email).first():
            hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
            admin = User(email=admin_email, password=hashed_pw, role='admin')
            db.session.add(admin)
            db.session.commit()
            
            profile = UserProfile(user_id=admin.id, full_name="System Admin")
            db.session.add(profile)
            
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_jobs()
