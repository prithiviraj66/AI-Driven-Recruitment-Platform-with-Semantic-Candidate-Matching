from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from models import db, User, UserProfile, CompanyProfile, Job, Application, Notification, EmailLog
from ml_engine import JobMatcher, ResumeParser
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['USE_SEMANTIC_MATCHING'] = True  # Set to True to enable SentenceTransformers deep learning model, False for instant TF-IDF

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'candidate')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        is_approved = (role != 'recruiter') # recruiters need approval
        
        user = User(email=email, password=hashed_password, role=role, is_approved=is_approved)
        db.session.add(user)
        db.session.commit()
        
        # Create an empty profile for the user
        profile = UserProfile(user_id=user.id, full_name="New User")
        db.session.add(profile)
        
        # Create CompanyProfile if user is recruiter
        if role == 'recruiter':
            company_name = request.form.get('company_name', 'My Company')
            website = request.form.get('website', '')
            industry = request.form.get('industry', '')
            description = request.form.get('description', '')
            company_profile = CompanyProfile(
                recruiter_id=user.id,
                company_name=company_name,
                website=website,
                industry=industry,
                description=description
            )
            db.session.add(company_profile)
            
        db.session.commit()
        
        if role == 'recruiter':
            flash('Account created successfully! It is pending admin approval/appointment.', 'warning')
        else:
            flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            if user.role == 'recruiter' and not user.is_approved:
                flash('Your recruiter account is pending admin approval/appointment.', 'warning')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

def get_candidate_matching_text(user):
    profile = user.profile
    if not profile:
        return ""
    
    parts = []
    if profile.full_name:
        parts.append(profile.full_name)
    if profile.skills:
        parts.append(profile.skills)
    if profile.bio:
        parts.append(profile.bio)
    if profile.experience:
        parts.append(profile.experience)
    if profile.education:
        parts.append(profile.education)
    if profile.location:
        parts.append(profile.location)
        
    # Append parsed resume PDF text if it exists
    if profile.resume_path and os.path.exists(profile.resume_path):
        try:
            from ml_engine import ResumeParser
            parser = ResumeParser()
            with open(profile.resume_path, 'rb') as f:
                resume_text = parser.extract_text_from_pdf(f)
                if resume_text:
                    parts.append(resume_text)
        except Exception as e:
            print(f"Error reading resume text for matching: {e}")
            
    return " ".join(parts)

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'recruiter':
        return redirect(url_for('recruiter_dashboard'))
        
    profile = current_user.profile
    jobs = Job.query.filter_by(is_active=True).all()
    # Filter out filled jobs
    jobs = [j for j in jobs if not j.is_filled]
    
    # Matching Engine
    matcher = JobMatcher(use_semantic=app.config.get('USE_SEMANTIC_MATCHING', False))
    user_text = get_candidate_matching_text(current_user)
    # Show all active jobs in dashboard
    recommendations = matcher.get_recommendations(user_text, jobs, top_n=len(jobs), user_skills=profile.skills)
    
    # Check if the user has updated their profile skills
    is_profile_updated = bool(profile.skills and profile.skills.strip())
    
    # Get user's applications
    applications = Application.query.filter_by(user_id=current_user.id).all()
    
    # Get candidate notifications (newest first)
    notifications = []
    if current_user.role == 'candidate':
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
        # Mark notifications as read
        unread_notifications = [n for n in notifications if not n.is_read]
        if unread_notifications:
            for n in unread_notifications:
                n.is_read = True
            db.session.commit()
    
    return render_template('dashboard.html', 
                          recommendations=recommendations, 
                          profile=profile,
                          applications=applications,
                          is_profile_updated=is_profile_updated,
                          notifications=notifications)

@app.route("/applied-jobs")
@login_required
def candidate_applied_jobs():
    if current_user.role != 'candidate':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.applied_at.desc()).all()
    return render_template('applied_jobs.html', applications=applications)

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    profile = current_user.profile
    if request.method == 'POST':
        profile.full_name = request.form.get('full_name')
        profile.bio = request.form.get('bio')
        profile.skills = request.form.get('skills')
        profile.experience = request.form.get('experience')
        profile.education = request.form.get('education')
        profile.location = request.form.get('location')
        
        # Handle resume upload
        resume = request.files.get('resume')
        if resume and resume.filename != '':
            path = os.path.join(app.config['UPLOAD_FOLDER'], f"user_{current_user.id}.pdf")
            resume.save(path)
            profile.resume_path = path
            
            # Auto-parse skills from resume
            parser = ResumeParser()
            with open(path, 'rb') as f:
                text = parser.extract_text_from_pdf(f)
                extracted_skills = parser.extract_skills(text)
                if extracted_skills:
                    # Combine with existing skills
                    current_skills = set([s.strip().lower() for s in (profile.skills or "").split(",") if s.strip()])
                    current_skills.update(extracted_skills)
                    profile.skills = ", ".join(current_skills)
        
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', profile=profile)

@app.route("/job/<int:job_id>")
@login_required
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    # Skill gap analysis
    parser = ResumeParser()
    user_skills = [s.strip().lower() for s in (current_user.profile.skills or "").split(",") if s.strip()]
    job_skills_list = [s.strip().lower() for s in (job.skills_required or "").split(",") if s.strip()]
    gap = parser.get_skill_gap(user_skills, job_skills_list)
    
    # Calculate match score
    matcher = JobMatcher(use_semantic=app.config.get('USE_SEMANTIC_MATCHING', False))
    user_text = get_candidate_matching_text(current_user)
    results = matcher.get_recommendations(user_text, [job], user_skills=current_user.profile.skills)
    score = results[0]['score'] if results else 0.0
    
    matched_skills = [s for s in job_skills_list if s in user_skills]
    
    return render_template('job_detail.html', job=job, gap=gap, score=score, matched_skills=matched_skills)

@app.route("/apply/<int:job_id>")
@login_required
def apply(job_id):
    # Check if already applied
    existing = Application.query.filter_by(user_id=current_user.id, job_id=job_id).first()
    if existing:
        flash('You have already applied for this job!', 'info')
    else:
        profile = current_user.profile
        job = Job.query.get_or_404(job_id)
        
        # Calculate matching score on submission
        matcher = JobMatcher(use_semantic=app.config.get('USE_SEMANTIC_MATCHING', False))
        user_text = get_candidate_matching_text(current_user)
        results = matcher.get_recommendations(user_text, [job], user_skills=profile.skills)
        score = results[0]['score'] if results else 0.0
        
        app_entry = Application(user_id=current_user.id, job_id=job_id, match_score=score)
        db.session.add(app_entry)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
    return redirect(url_for('dashboard'))

# --- Recruiter Suite ---

@app.route("/recruiter")
@login_required
def recruiter_dashboard():
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    stats = {
        'total_users': User.query.filter_by(role='candidate').count(),
        'total_jobs': Job.query.filter_by(posted_by=current_user.id).count(),
        'total_applications': Application.query.join(Job).filter(Job.posted_by == current_user.id).count(),
        'active_jobs': Job.query.filter_by(posted_by=current_user.id, is_active=True).count()
    }
    
    # Skill demand analysis
    all_jobs = Job.query.filter_by(posted_by=current_user.id).all()
    skill_counts = {}
    for j in all_jobs:
        skills = [s.strip().lower() for s in j.skills_required.split(',') if s.strip()]
        for s in skills:
            skill_counts[s] = skill_counts.get(s, 0) + 1
    
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Calculate status distribution counts for the logged-in recruiter's jobs
    status_counts = {
        'Applied': Application.query.join(Job).filter(Job.posted_by == current_user.id, Application.status.in_(['Applied', 'applied'])).count(),
        'Selected': Application.query.join(Job).filter(Job.posted_by == current_user.id, Application.status.in_(['Selected', 'Appointed'])).count(),
        'Interview': Application.query.join(Job).filter(Job.posted_by == current_user.id, Application.status.in_(['Interview', 'Interviewing', 'interview'])).count(),
        'Exam': Application.query.join(Job).filter(Job.posted_by == current_user.id, Application.status == 'Exam').count(),
        'Rejected': Application.query.join(Job).filter(Job.posted_by == current_user.id, Application.status == 'Rejected').count()
    }
    
    # Distinct candidates count who applied to this recruiter's jobs
    candidates_count = User.query.filter_by(role='candidate').join(Application).join(Job).filter(Job.posted_by == current_user.id).distinct().count()
    
    # Fetch recent simulated email logs
    recent_emails = EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(10).all()
    
    return render_template('recruiter/dashboard.html', stats=stats, top_skills=top_skills, all_jobs=all_jobs, status_counts=status_counts, candidates_count=candidates_count, recent_emails=recent_emails)

@app.route("/recruiter/profile", methods=['GET', 'POST'])
@login_required
def recruiter_profile():
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
        
    profile = current_user.company_profile
    if not profile:
        profile = CompanyProfile(recruiter_id=current_user.id, company_name="My Company")
        db.session.add(profile)
        db.session.commit()
        
    if request.method == 'POST':
        profile.company_name = request.form.get('company_name')
        profile.website = request.form.get('website')
        profile.industry = request.form.get('industry')
        profile.description = request.form.get('description')
        
        db.session.commit()
        flash('Company profile updated successfully!', 'success')
        return redirect(url_for('recruiter_profile'))
        
    return render_template('recruiter/profile.html', profile=profile)

@app.route("/recruiter/jobs")
@login_required
def recruiter_jobs():
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    jobs = Job.query.filter_by(posted_by=current_user.id).order_by(Job.posted_at.desc()).all()
    return render_template('recruiter/jobs.html', jobs=jobs)

@app.route("/recruiter/add_job", methods=['GET', 'POST'])
@login_required
def recruiter_add_job():
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        company_name = current_user.company_profile.company_name if current_user.company_profile else request.form.get('company', 'My Company')
        job = Job(
            title=request.form.get('title'),
            company=company_name,
            description=request.form.get('description'),
            skills_required=request.form.get('skills_required'),
            location=request.form.get('location'),
            salary=request.form.get('salary'),
            job_type=request.form.get('job_type', 'Full-time'),
            experience_level=request.form.get('experience_level', 'Entry-level'),
            posted_by=current_user.id,
            vacancies=request.form.get('vacancies', 1, type=int)
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('recruiter_jobs'))
    return render_template('recruiter/add_job.html')

@app.route("/recruiter/job/<int:job_id>/edit", methods=['GET', 'POST'])
@login_required
def recruiter_edit_job(job_id):
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    job = Job.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('Access denied! You do not own this job listing.', 'danger')
        return redirect(url_for('recruiter_jobs'))
        
    if request.method == 'POST':
        job.title = request.form.get('title')
        if current_user.company_profile:
            job.company = current_user.company_profile.company_name
        else:
            job.company = request.form.get('company')
        job.description = request.form.get('description')
        job.skills_required = request.form.get('skills_required')
        job.location = request.form.get('location')
        job.salary = request.form.get('salary')
        job.job_type = request.form.get('job_type')
        job.experience_level = request.form.get('experience_level')
        job.vacancies = request.form.get('vacancies', 1, type=int)
        job.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('recruiter_jobs'))
    return render_template('recruiter/edit_job.html', job=job)

@app.route("/recruiter/job/<int:job_id>/delete")
@login_required
def recruiter_delete_job(job_id):
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    job = Job.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('Access denied! You do not own this job listing.', 'danger')
        return redirect(url_for('recruiter_jobs'))
        
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully!', 'info')
    return redirect(url_for('recruiter_jobs'))

@app.route("/recruiter/candidates")
@login_required
def recruiter_candidates():
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    # Show only candidates who have applied to jobs posted by this recruiter
    candidates = User.query.filter_by(role='candidate').join(Application).join(Job).filter(Job.posted_by == current_user.id).distinct().all()
    return render_template('recruiter/candidates.html', candidates=candidates)

@app.route("/recruiter/candidate/<int:user_id>")
@login_required
def recruiter_candidate_profile(user_id):
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    candidate = User.query.get_or_404(user_id)
    if candidate.role != 'candidate':
        flash('Invalid candidate.', 'danger')
        return redirect(url_for('recruiter_candidates'))
    
    # Get candidate applications for jobs posted by this recruiter
    applications = Application.query.join(Job).filter(Application.user_id == candidate.id, Job.posted_by == current_user.id).order_by(Application.applied_at.desc()).all()
    
    return render_template('recruiter/candidate_profile.html', candidate=candidate, applications=applications)

@app.route("/recruiter/resume/<int:user_id>")
@login_required
def recruiter_view_resume(user_id):
    if current_user.role not in ['recruiter', 'admin'] and current_user.id != user_id:
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    if not user.profile or not user.profile.resume_path:
        flash('No resume uploaded.', 'info')
        return redirect(request.referrer or url_for('dashboard'))
        
    directory = os.path.abspath(app.config['UPLOAD_FOLDER'])
    filename = os.path.basename(user.profile.resume_path)
    
    if not os.path.exists(os.path.join(directory, filename)):
        flash('Resume file not found on server.', 'danger')
        return redirect(request.referrer or url_for('dashboard'))
        
    return send_from_directory(directory, filename)

@app.route("/recruiter/applications")
@login_required
def recruiter_applications():
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    # Show only applications with status 'Applied'
    applications = Application.query.join(Job).filter(
        Job.posted_by == current_user.id,
        Application.status.in_(['Applied', 'applied'])
    ).order_by(Application.applied_at.desc()).all()
    return render_template('recruiter/new_applications.html', applications=applications)

@app.route("/recruiter/interviews")
@login_required
def recruiter_interviews():
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    # Show only applications with status 'Interview'
    applications = Application.query.join(Job).filter(
        Job.posted_by == current_user.id,
        Application.status.in_(['Interview', 'Interviewing', 'interview'])
    ).order_by(Application.applied_at.desc()).all()
    return render_template('recruiter/interviews.html', applications=applications)

@app.route("/recruiter/appointed")
@login_required
def recruiter_appointed():
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    # Show only applications with status 'Appointed' or 'Selected'
    applications = Application.query.join(Job).filter(
        Job.posted_by == current_user.id,
        Application.status.in_(['Appointed', 'Selected'])
    ).order_by(Application.applied_at.desc()).all()
    return render_template('recruiter/appointed.html', applications=applications)

@app.route("/recruiter/exams")
@login_required
def recruiter_exams():
    if current_user.role != 'recruiter':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    # Show only applications with status 'Exam'
    applications = Application.query.join(Job).filter(
        Job.posted_by == current_user.id,
        Application.status == 'Exam'
    ).order_by(Application.applied_at.desc()).all()
    return render_template('recruiter/exams.html', applications=applications)

@app.route("/recruiter/application/<int:app_id>/status", methods=['POST'])
@login_required
def recruiter_update_app_status(app_id):
    if current_user.role != 'recruiter':
        return jsonify({'error': 'Unauthorized'}), 403
    
    application = Application.query.get_or_404(app_id)
    if application.job.posted_by != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    new_status = request.form.get('status')
    if new_status:
        if new_status == 'Rejected':
            msg = f"Your application for '{application.job.title}' at '{application.job.company}' has been rejected."
            notif = Notification(user_id=application.user_id, message=msg)
            db.session.add(notif)
            
            print("\n" + "="*60)
            print("SMTP [SIMULATED]: Sending status update email...")
            print(f"To: {application.user.email}")
            print(f"Subject: Application Update: {application.job.title} at {application.job.company}")
            print(f"Body: Hello,\n\n{msg}\n\nBest regards,\nJobMatch Team")
            print("="*60 + "\n")
            
            email_subject = f"Application Update: {application.job.title} at {application.job.company}"
            email_body = f"Hello,\n\n{msg}\n\nBest regards,\nJobMatch Team"
            email_log = EmailLog(recipient=application.user.email, subject=email_subject, body=email_body)
            db.session.add(email_log)
            
            db.session.delete(application)
            db.session.commit()
            
            flash('Application rejected and permanently removed from tracking.', 'warning')
            return redirect(url_for('recruiter_applications'))
        else:
            application.status = new_status
            
            msg = f"Your application for '{application.job.title}' at '{application.job.company}' has been updated to '{new_status}'."
            notif = Notification(user_id=application.user_id, message=msg)
            db.session.add(notif)
            
            print("\n" + "="*60)
            print("SMTP [SIMULATED]: Sending status update email...")
            print(f"To: {application.user.email}")
            print(f"Subject: Application Update: {application.job.title} at {application.job.company}")
            print(f"Body: Hello,\n\n{msg}\n\nBest regards,\nJobMatch Team")
            print("="*60 + "\n")
            
            email_subject = f"Application Update: {application.job.title} at {application.job.company}"
            email_body = f"Hello,\n\n{msg}\n\nBest regards,\nJobMatch Team"
            email_log = EmailLog(recipient=application.user.email, subject=email_subject, body=email_body)
            db.session.add(email_log)
            db.session.commit()
            
            flash(f'Status updated to {new_status}', 'success')
            
            if new_status in ['Interview', 'Interviewing']:
                return redirect(url_for('recruiter_interviews'))
            elif new_status == 'Exam':
                return redirect(url_for('recruiter_exams'))
            elif new_status == 'Appointed':
                return redirect(url_for('recruiter_appointed'))
            
    return redirect(url_for('recruiter_applications'))


# --- Admin Suite ---

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    stats = {
        'total_candidates': User.query.filter_by(role='candidate').count(),
        'total_recruiters': User.query.filter_by(role='recruiter').count(),
        'total_jobs': Job.query.count(),
        'total_applications': Application.query.count(),
        'active_jobs': Job.query.filter_by(is_active=True).count()
    }
    
    pending_recruiters = User.query.filter_by(role='recruiter', is_approved=False).order_by(User.id.desc()).all()
    approved_recruiters = User.query.filter_by(role='recruiter', is_approved=True).order_by(User.id.desc()).all()
    recent_emails = EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', stats=stats, pending_recruiters=pending_recruiters, approved_recruiters=approved_recruiters, recent_emails=recent_emails)

@app.route("/admin/recruiter/<int:recruiter_id>/approve", methods=['POST'])
@login_required
def admin_approve_recruiter(recruiter_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
        
    recruiter = User.query.get_or_404(recruiter_id)
    if recruiter.role != 'recruiter':
        flash('Invalid user type for approval.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    recruiter.is_approved = True
    
    company_name = recruiter.company_profile.company_name if recruiter.company_profile else "your company"
    msg = f"Your recruiter account for '{company_name}' has been approved/appointed by the Platform Administrator. You can now log in and post job listings."
    
    print("\n" + "="*60)
    print("SMTP [SIMULATED]: Sending recruiter approval email...")
    print(f"To: {recruiter.email}")
    print(f"Subject: Recruiter Account Approved: {company_name}")
    print(f"Body: Hello,\n\n{msg}\n\nBest regards,\nJobMatch Team")
    print("="*60 + "\n")
    
    email_log = EmailLog(
        recipient=recruiter.email, 
        subject=f"Recruiter Account Approved: {company_name}", 
        body=f"Hello,\n\n{msg}\n\nBest regards,\nJobMatch Team"
    )
    db.session.add(email_log)
    db.session.commit()
    
    flash(f"Recruiter account for '{company_name}' has been successfully approved/appointed!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/recruiter/<int:recruiter_id>/disapprove", methods=['POST'])
@login_required
def admin_disapprove_recruiter(recruiter_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
        
    recruiter = User.query.get_or_404(recruiter_id)
    if recruiter.role != 'recruiter':
        flash('Invalid user type.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    recruiter.is_approved = False
    db.session.commit()
    
    company_name = recruiter.company_profile.company_name if recruiter.company_profile else "your company"
    flash(f"Revoked approval for '{company_name}'.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/recruiter/<int:recruiter_id>")
@login_required
def admin_recruiter_profile(recruiter_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
        
    recruiter = User.query.get_or_404(recruiter_id)
    if recruiter.role != 'recruiter':
        flash('Invalid user type.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    jobs = Job.query.filter_by(posted_by=recruiter.id).order_by(Job.posted_at.desc()).all()
    return render_template('admin/recruiter_profile.html', recruiter=recruiter, jobs=jobs)

@app.route("/admin/recruiter/<int:recruiter_id>/delete", methods=['POST'])
@login_required
def admin_delete_recruiter(recruiter_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
        
    recruiter = User.query.get_or_404(recruiter_id)
    if recruiter.role != 'recruiter':
        flash('Invalid user type.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    # Cascade deletion manually to avoid sqlite constraint failures
    jobs = Job.query.filter_by(posted_by=recruiter.id).all()
    for job in jobs:
        Application.query.filter_by(job_id=job.id).delete()
        db.session.delete(job)
        
    Application.query.filter_by(user_id=recruiter.id).delete()
    Notification.query.filter_by(user_id=recruiter.id).delete()
    
    if recruiter.profile:
        db.session.delete(recruiter.profile)
    if recruiter.company_profile:
        db.session.delete(recruiter.company_profile)
        
    db.session.delete(recruiter)
    db.session.commit()
    
    flash('Recruiter and all associated jobs/applications have been successfully deleted.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/jobs")
@login_required
def admin_jobs():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    jobs = Job.query.order_by(Job.posted_at.desc()).all()
    # Filter out filled jobs
    jobs = [j for j in jobs if not j.is_filled]
    return render_template('admin/jobs.html', jobs=jobs)

@app.route("/admin/job/<int:job_id>/delete")
@login_required
def admin_delete_job(job_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
        
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job listing moderated and successfully deleted.', 'info')
    return redirect(url_for('admin_jobs'))

@app.route("/admin/candidates")
@login_required
def admin_candidates():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    candidates = User.query.filter_by(role='candidate').order_by(User.id.desc()).all()
    return render_template('admin/candidates.html', candidates=candidates)

@app.route("/admin/candidate/<int:user_id>")
@login_required
def admin_candidate_profile(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    candidate = User.query.get_or_404(user_id)
    if candidate.role != 'candidate':
        flash('Invalid candidate.', 'danger')
        return redirect(url_for('admin_candidates'))
    
    # Admin has access to all applications globally
    applications = Application.query.filter_by(user_id=candidate.id).order_by(Application.applied_at.desc()).all()
    
    return render_template('admin/candidate_profile.html', candidate=candidate, applications=applications)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
    if app.config.get('USE_SEMANTIC_MATCHING', False):
        import threading
        def background_preload():
            try:
                from ml_engine import JobMatcher
                JobMatcher.preload_model()
            except Exception as e:
                print(f"Background preload failed: {e}")
        
        thread = threading.Thread(target=background_preload, daemon=True)
        thread.start()
        
    app.run(debug=True)
