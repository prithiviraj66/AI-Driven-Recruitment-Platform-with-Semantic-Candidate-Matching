# AI-Driven Recruitment Platform with Semantic Candidate Matching

An AI-powered recruitment platform that intelligently matches candidates to job postings using Semantic Candidate Matching. Instead of relying only on keyword matching, the system analyzes the meaning and context of resumes and job descriptions to recommend the most suitable candidates. The platform streamlines the hiring process for recruiters while helping job seekers find relevant opportunities.

---

##  Overview & Screenshots

| Home Page | Candidate Dashboard |

 <img width="1916" height="1078" alt="Screenshot 2026-07-11 155901" src="https://github.com/user-attachments/assets/a7e7746e-f7de-4c7e-9eff-13c17a5d6f09" />
 <img width="1917" height="1078" alt="Screenshot 2026-07-11 154709" src="https://github.com/user-attachments/assets/e2595f69-af31-4750-a897-5d06c3c1648f" />

| Recruiter Dashboard |
 <img width="1917" height="1078" alt="Screenshot 2026-07-11 154833" src="https://github.com/user-attachments/assets/04d3feab-9bd3-48b3-9af8-3fdc866458bc" />

| Admin Dashboard |
<img width="1917" height="1075" alt="Screenshot 2026-07-11 154637" src="https://github.com/user-attachments/assets/053000b4-187f-4687-81b8-49a998544c4a" /> 


---

##  Features

###  Candidate Module
* User registration and secure login.
* Upload resume in PDF format.
* Browse available job openings.
* Apply for jobs.
* View applied jobs and application status.
* Candidate dashboard.

###  Recruiter Module
* Recruiter registration and login.
* Create, update, and manage job postings.
* View candidate applications.
* AI-powered candidate ranking.
* Recruiter dashboard.

###  Admin Module
* Manage candidates.
* Manage recruiters.
* Manage job postings.
* Monitor platform activity.
* Administrative dashboard.

###  AI Semantic Matching
* Resume parsing from PDF files.
* Text preprocessing.
* Semantic similarity between resumes and job descriptions.
* Intelligent candidate ranking.
* Improved hiring accuracy compared to keyword-based matching.

---

##  Technology Stack

| Category | Technologies |
| :--- | :--- |
| **Backend** | Python, Flask |
| **Database** | SQLite, SQLAlchemy |
| **Authentication** | Flask-Login, Flask-Bcrypt |
| **Machine Learning** | Scikit-learn, Sentence-Transformers |
| **Resume Processing** | PyPDF2 |
| **Data Processing** | Pandas |
| **Frontend** | HTML, CSS, JavaScript, Jinja2 |

---

##  Project Structure

```text
AI-Driven-Recruitment-Platform-with-Semantic-Candidate-Matching/
│
├── job/
│   ├── app/
│   │   ├── static/               # CSS, JS, and image assets
│   │   ├── templates/            # HTML templates for user interfaces
│   │   ├── uploads/              # Directory for uploaded resumes
│   │   ├── main.py               # Flask application entry point & routing
│   │   ├── ml_engine.py          # AI matching models & PDF parsing logic
│   │   ├── models.py             # Database schemas & relationships
│   │   ├── populate_dummy_data.py # Seed script for complete profiles & applications
│   │   ├── reset_db.py           # Seed script for resetting and building default admin/jobs
│   │   ├── seed.py               # Alternate database seeding script
│   │   └── requirements.txt      # Dependency list
│   └── instance/                 # Local development database instances
└── README.md                     # Documentation
```

---

##  Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/AI-Driven-Recruitment-Platform-with-Semantic-Candidate-Matching.git
```

### 2. Navigate to the Project
```bash
cd AI-Driven-Recruitment-Platform-with-Semantic-Candidate-Matching/job/app
```

### 3. Create & Activate Virtual Environment

* **On Windows:**
  ```powershell
  python -m venv venv
  venv\Scripts\activate
  ```

* **On Linux / macOS:**
  ```bash
  python -m venv venv
  source venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Setup Database & Seed Initial Data (Optional)
Before running, you can seed candidate and admin mock data:
```bash
python reset_db.py
# or
python populate_dummy_data.py
```

### 6. Run the Application
```bash
python main.py
```

---

##  AI Matching Workflow

```text
      ┌─────────────────────────┐
      │      Resume Upload      │
      └────────────┬────────────┘
                   │
                   ▼
      ┌─────────────────────────┐
      │   PDF Text Extraction   │
      └────────────┬────────────┘
                   │
                   ▼
      ┌─────────────────────────┐
      │  Text Clean & Preprocess│
      └────────────┬────────────┘
                   │
                   ▼
      ┌─────────────────────────┐
      │   Feature Extraction    │
      └────────────┬────────────┘
                   │
                   ▼
      ┌─────────────────────────┐
      │   Semantic Similarity   │
      └────────────┬────────────┘
                   │
                   ▼
      ┌─────────────────────────┐
      │    Candidate Ranking    │
      └────────────┬────────────┘
                   │
                   ▼
      ┌─────────────────────────┐
      │ Recruiter Recommendation│
      └─────────────────────────┘
```

---

##  Requirements

* Python 3.10+
* Flask
* Flask-Bcrypt
* Flask-Login
* Flask-SQLAlchemy
* Pandas
* Scikit-learn
* Sentence-Transformers (optional for Semantic Deep Learning, defaults to TF-IDF if unavailable)
* PyPDF2
