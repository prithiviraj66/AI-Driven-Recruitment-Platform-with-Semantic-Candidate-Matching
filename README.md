#AI-Driven Recruitment Platform with Semantic Candidate Matching

An AI-powered recruitment platform that intelligently matches candidates to job postings using **Semantic Candidate Matching**. Instead of relying only on keyword matching, the system analyzes the meaning and context of resumes and job descriptions to recommend the most suitable candidates. The platform streamlines the hiring process for recruiters while helping job seekers find relevant opportunities.

---

## Features

### Candidate Module
- User registration and secure login
- Upload resume in PDF format
- Browse available job openings
- Apply for jobs
- View applied jobs and application status
- Candidate dashboard

### Recruiter Module
- Recruiter registration and login
- Create, update, and manage job postings
- View candidate applications
- AI-powered candidate ranking
- Recruiter dashboard

### Admin Module
- Manage candidates
- Manage recruiters
- Manage job postings
- Monitor platform activity
- Administrative dashboard

### AI Semantic Matching
- Resume parsing from PDF files
- Text preprocessing
- Semantic similarity between resumes and job descriptions
- Intelligent candidate ranking
- Improved hiring accuracy compared to keyword-based matching

---

# Technology Stack

| Category | Technologies |
|----------|--------------|
| Backend | Python, Flask |
| Database | SQLite, SQLAlchemy |
| Authentication | Flask-Login, Flask-Bcrypt |
| Machine Learning | Scikit-learn |
| Resume Processing | PyPDF2 |
| Data Processing | Pandas |
| Frontend | HTML, CSS, JavaScript, Jinja2 |

---

# Project Structure

```
AI-Driven-Recruitment-Platform-with-Semantic-Candidate-Matching/
│
├── app/
│   ├── static/
│   ├── templates/
│   ├── uploads/
│   ├── main.py
│   ├── ml_engine.py
│   ├── models.py
│   ├── populate_dummy_data.py
│   └── requirements.txt
│
└── instance/
```

# Installation
### 1. Clone the Repository

```bash
git clone https://github.com/your-username/AI-Driven-Recruitment-Platform-with-Semantic-Candidate-Matching.git
```
### 2. Navigate to the Project
```bash
cd AI-Driven-Recruitment-Platform-with-Semantic-Candidate-Matching/job/app
```
### 3. Create Virtual Environment

```bash
python -m venv venv
```
Activate the environment:
**Windows**

```bash
venv\Scripts\activate
```
**Linux / macOS**
```bash
source venv/bin/activate
```
### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
### 5. Run the Application
```bash
python main.py
```
---

#  AI Matching Workflow
```
Resume Upload
      │
      ▼
PDF Text Extraction
      │
      ▼
Text Cleaning & Preprocessing
      │
      ▼
Feature Extraction
      │
      ▼
Semantic Similarity Calculation
      │
      ▼
Candidate Ranking
      │
      ▼
Recruiter Recommendation
```
# 📸 Screenshots

Add screenshots of:

- Home Page
- Candidate Dashboard
- Recruiter Dashboard
- Admin Dashboard
- Job Posting Page
- Candidate Ranking Results

# 📦 Requirements

- Python 3.10+
- Flask
- Flask-Bcrypt
- Flask-Login
- Flask-SQLAlchemy
- Pandas
- Scikit-learn
- PyPDF2

---

# 👨‍💻 Author

**Prithiviraj S**

AI & Machine Learning Enthusiast

