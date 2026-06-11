from main import app, db, bcrypt
from models import User, UserProfile, Job
import os

def reset_and_seed():
    with app.app_context():
        # Drop all tables and recreate them
        print("Dropping all tables...")
        db.drop_all()
        print("Recreating tables with new schema...")
        db.create_all()
        
        # 1. Create the new Admin User
        admin_email = "ps8058@srmist.edu.in"
        print(f"Creating new admin: {admin_email}")
        hashed_pw = bcrypt.generate_password_hash("123456").decode('utf-8')
        admin = User(email=admin_email, password=hashed_pw, role='admin')
        db.session.add(admin)
        db.session.flush() # To get admin.id
        
        profile = UserProfile(user_id=admin.id, full_name="System Administrator")
        db.session.add(profile)
        
        # 2. Add some sample jobs with new fields
        jobs_data = [
            {
                "title": "Senior Cloud Architect",
                "company": "SkyNet Systems",
                "description": "Lead our migration to multi-cloud infrastructure.",
                "skills_required": "aws, azure, kubernetes, terraform",
                "location": "Remote",
                "salary": "$160k - $200k",
                "job_type": "Full-time",
                "experience_level": "Senior"
            },
            {
                "title": "Junior Python Developer",
                "company": "StartUp Flow",
                "description": "Join our fast-paced backend team.",
                "skills_required": "python, flask, git",
                "location": "San Francisco, CA",
                "salary": "$80k - $110k",
                "job_type": "Full-time",
                "experience_level": "Junior"
            },
            {
                "title": "ML Research Intern",
                "company": "DeepMind Lab",
                "description": "Collaborate on cutting-edge AI research.",
                "skills_required": "python, pytorch, research",
                "location": "London, UK",
                "salary": "Stipend",
                "job_type": "Internship",
                "experience_level": "Entry-level"
            }
        ]
        
        for job_info in jobs_data:
            job = Job(**job_info)
            db.session.add(job)
            
        db.session.commit()
        print("Database reset and seeded successfully!")

if __name__ == "__main__":
    reset_and_seed()
