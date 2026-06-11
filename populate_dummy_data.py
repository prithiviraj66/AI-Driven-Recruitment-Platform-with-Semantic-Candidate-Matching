from main import app, db, bcrypt
from models import Job, User, UserProfile, Application
import random

def populate_data():
    with app.app_context():
        # Add 7 detailed jobs
        jobs_data = [
            {
                "title": "Senior Python Developer",
                "company": "TechNova Solutions",
                "description": "We are looking for a Python expert to lead our backend team in building scalable cloud services. You will work with Flask, AWS, and Docker.",
                "skills_required": "python, flask, aws, docker, sql",
                "location": "San Francisco, CA",
                "salary": "$140,000 - $180,000",
                "job_type": "Full-time",
                "experience_level": "Senior"
            },
            {
                "title": "Frontend Engineer (React)",
                "company": "DesignSphere",
                "description": "Join our creative team to build stunning user interfaces. Must be proficient in React, CSS, and modern web design principles.",
                "skills_required": "javascript, react, html, css, tailwind",
                "location": "Remote",
                "salary": "$110,000 - $150,000",
                "job_type": "Contract",
                "experience_level": "Mid-level"
            },
            {
                "title": "Data Scientist",
                "company": "Insight Analytics",
                "description": "Analyze large datasets and build predictive models using machine learning. Experience with Pandas, Scikit-learn, and NLP is required.",
                "skills_required": "python, pandas, scikit-learn, nlp, sql, machine learning",
                "location": "New York, NY",
                "salary": "$130,000 - $170,000",
                "job_type": "Full-time",
                "experience_level": "Senior"
            },
            {
                "title": "DevOps Engineer",
                "company": "CloudScale",
                "description": "Automate our infrastructure and optimize deployment pipelines using Kubernetes and Terraform.",
                "skills_required": "aws, linux, kubernetes, docker, git, terraform",
                "location": "Austin, TX",
                "salary": "$125,000 - $165,000",
                "job_type": "Full-time",
                "experience_level": "Mid-level"
            },
            {
                "title": "Full Stack Developer",
                "company": "Startup Hub",
                "description": "A versatile developer who can handle both front-end (React) and back-end (Django/Node).",
                "skills_required": "python, javascript, django, node.js, react, mongodb",
                "location": "Seattle, WA",
                "salary": "$115,000 - $155,000",
                "job_type": "Full-time",
                "experience_level": "Entry-level"
            },
            {
                "title": "ML Research Intern",
                "company": "AIVision",
                "description": "Assist in building high-performance deep learning models for computer vision.",
                "skills_required": "python, deep learning, pytorch, tensorflow, linux",
                "location": "Boston, MA",
                "salary": "Stipend",
                "job_type": "Internship",
                "experience_level": "Entry-level"
            },
            {
                "title": "Product Designer",
                "company": "UserFirst",
                "description": "Design user-centric products and conduct UX research.",
                "skills_required": "ui/ux, figma, design thinking, html",
                "location": "Remote",
                "salary": "$90,000 - $130,000",
                "job_type": "Full-time",
                "experience_level": "Mid-level"
            }
        ]

        inserted_jobs = []
        for job_info in jobs_data:
            job = Job(**job_info)
            db.session.add(job)
            inserted_jobs.append(job)
        
        db.session.flush() # flush to get job defaults like IDs

        all_jobs = Job.query.all()

        # Add 5 diverse candidates
        candidates_data = [
            {
                "email": "sarah.j@example.com",
                "name": "Sarah Jenkins",
                "location": "San Francisco, CA",
                "bio": "Backend specialist with heavy focus on scalable systems.",
                "skills": "python, flask, django, aws, sql",
                "experience": "4 years building Python APIs."
            },
            {
                "email": "mike.r@example.com",
                "name": "Mike Ross",
                "location": "New York, NY",
                "bio": "Data enthusiast making sense of numbers.",
                "skills": "python, pandas, numpy, scikit-learn",
                "experience": "3 years as Data Analyst."
            },
            {
                "email": "lucy.designer@example.com",
                "name": "Lucy Bennett",
                "location": "Remote",
                "bio": "UI/UX Designer who loves creating beautiful web experiences.",
                "skills": "figma, ui/ux, photoshop, css, html",
                "experience": "5 years designing products."
            },
            {
                "email": "devops.dan@example.com",
                "name": "Daniel Stevens",
                "location": "Austin, TX",
                "bio": "Pipeline builder and infra-as-code believer.",
                "skills": "kubernetes, docker, terraform, aws, linux",
                "experience": "Senior DevOps Engineer."
            },
            {
                "email": "newgrad.tim@example.com",
                "name": "Tim Baker",
                "location": "Seattle, WA",
                "bio": "Recent CS grad looking for front-end or full-stack role.",
                "skills": "javascript, react, html, css, node.js",
                "experience": "Internships at tech startups."
            }
        ]

        hashed_pw = bcrypt.generate_password_hash("password123").decode('utf-8')
        
        candidate_users = []
        for c in candidates_data:
            if not User.query.filter_by(email=c["email"]).first():
                user = User(email=c["email"], password=hashed_pw, role='candidate')
                db.session.add(user)
                db.session.flush()

                profile = UserProfile(
                    user_id=user.id,
                    full_name=c["name"],
                    location=c["location"],
                    bio=c["bio"],
                    skills=c["skills"],
                    experience=c["experience"]
                )
                db.session.add(profile)
                candidate_users.append(user)

        db.session.commit()

        # Create Applications (Randomized)
        statuses = ['Applied', 'Interviewing', 'Rejected', 'Selected']
        added_apps = 0
        
        candidates = [u for u in candidate_users]
        if not candidates:
            candidates = User.query.filter_by(role='candidate').all()
            
        for user in candidates:
            # Each tech candidate applies to 2-4 jobs matching their skills roughly
            if "python" in user.profile.skills:
                jobs_to_apply = [j for j in all_jobs if "python" in j.skills_required]
            elif "react" in user.profile.skills or "figma" in user.profile.skills:
                jobs_to_apply = [j for j in all_jobs if "react" in j.skills_required or "ui/ux" in j.skills_required]
            else:
                jobs_to_apply = [j for j in all_jobs if "aws" in j.skills_required]
                
            jobs_to_apply += random.sample(all_jobs, min(2, len(all_jobs))) # add some random ones
            jobs_to_apply = list(set(jobs_to_apply))
            
            for job in jobs_to_apply[:3]: # apply up to 3
                if not Application.query.filter_by(user_id=user.id, job_id=job.id).first():
                    score = random.uniform(60.0, 98.5)
                    status = random.choice(statuses)
                    app_entry = Application(
                        user_id=user.id, 
                        job_id=job.id, 
                        status=status, 
                        match_score=round(score, 1)
                    )
                    db.session.add(app_entry)
                    added_apps += 1
            
        db.session.commit()
        print(f"Dummy data added successfully! Inserted {len(inserted_jobs)} jobs, {len(candidate_users)} users, {added_apps} applications.")

if __name__ == "__main__":
    populate_data()
