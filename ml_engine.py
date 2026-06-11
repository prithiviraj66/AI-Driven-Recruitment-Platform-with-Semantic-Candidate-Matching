import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import re

def normalize_skill(skill):
    if not skill:
        return ""
    skill = skill.lower().strip()
    # Replace common variations
    skill = re.sub(r'\bjs\b|\.js\b', '', skill)
    skill = skill.replace('-', '').replace(' ', '')
    return skill

class JobMatcher:
    _model = None  # Class-level cache to ensure the model is loaded only once
    _job_embeddings_cache = {}  # Cache map of job.id -> (job_text_representation, embedding)
    _user_embeddings_cache = {}  # Cache map of user_text -> embedding

    @classmethod
    def preload_model(cls):
        try:
            from sentence_transformers import SentenceTransformer
            if cls._model is None:
                print("Preloading sentence-transformers model (all-MiniLM-L6-v2) in background...")
                cls._model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Background model preloading completed successfully!")
        except Exception as e:
            print(f"Failed to preload model: {e}")

    def __init__(self, use_semantic=True):
        self.use_semantic = use_semantic
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
        if self.use_semantic:
            # Check if sentence-transformers is available
            try:
                import sentence_transformers
            except ImportError:
                print("sentence-transformers not installed, falling back to TF-IDF matching.")
                self.use_semantic = False

    def get_recommendations(self, user_text, jobs, top_n=5, user_skills=None):
        """
        user_text: combined skills, bio, experience
        jobs: list of job objects (dict or SQLAlchemy model)
        user_skills: list or comma-separated string of user's skills
        """
        if not jobs:
            return []
            
        # Parse user skills
        candidate_skills = []
        if user_skills:
            if isinstance(user_skills, str):
                candidate_skills = [s.strip().lower() for s in user_skills.split(',') if s.strip()]
            elif isinstance(user_skills, list):
                candidate_skills = [s.strip().lower() for s in user_skills if s.strip()]
        
        # Fallback: if no user_skills provided/extracted, parse them from user_text
        if not candidate_skills:
            candidate_skills = ResumeParser().extract_skills(user_text)
            
        candidate_skills_normalized = {normalize_skill(s) for s in candidate_skills if s}
        
        # Calculate semantic or TF-IDF text similarity
        cosine_sim = None
        use_semantic_run = self.use_semantic
        
        if use_semantic_run:
            try:
                from sentence_transformers import SentenceTransformer
                if JobMatcher._model is None:
                    # Load model lazily on first match request to prevent blocking server startup
                    print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
                    JobMatcher._model = SentenceTransformer('all-MiniLM-L6-v2')
                    print("Model loaded successfully!")
                
                # Calculate user profile embedding using caching
                if user_text in JobMatcher._user_embeddings_cache:
                    user_embedding = JobMatcher._user_embeddings_cache[user_text]
                else:
                    user_embedding = JobMatcher._model.encode([user_text])
                    JobMatcher._user_embeddings_cache[user_text] = user_embedding
                
                # Retrieve or compute job embeddings using caching
                job_embeddings_list = []
                jobs_to_encode = []
                jobs_to_encode_indices = []
                
                for idx, j in enumerate(jobs):
                    job_text = f"{j.title} {j.description} {j.skills_required}"
                    # If job is cached and its details haven't changed, reuse the embedding
                    if j.id in JobMatcher._job_embeddings_cache and JobMatcher._job_embeddings_cache[j.id][0] == job_text:
                        job_embeddings_list.append(JobMatcher._job_embeddings_cache[j.id][1])
                    else:
                        job_embeddings_list.append(None) # Placeholder
                        jobs_to_encode.append(job_text)
                        jobs_to_encode_indices.append(idx)
                
                # Compute missing embeddings in a single batch
                if jobs_to_encode:
                    print(f"Computing embeddings for {len(jobs_to_encode)} uncached jobs...")
                    new_embeddings = JobMatcher._model.encode(jobs_to_encode)
                    for new_idx, orig_idx in enumerate(jobs_to_encode_indices):
                        j = jobs[orig_idx]
                        job_text = jobs_to_encode[new_idx]
                        embedding = new_embeddings[new_idx]
                        # Cache it
                        JobMatcher._job_embeddings_cache[j.id] = (job_text, embedding)
                        job_embeddings_list[orig_idx] = embedding
                
                import numpy as np
                job_embeddings = np.array(job_embeddings_list)
                
                # Calculate cosine similarity
                cosine_sim = cosine_similarity(user_embedding, job_embeddings).flatten()
            except Exception as e:
                print(f"Error in Semantic Matcher, falling back to TF-IDF: {e}")
                use_semantic_run = False

        if not use_semantic_run or cosine_sim is None:
            # Fallback TF-IDF Logic
            job_texts = [f"{j.title} {j.description} {j.skills_required}" for j in jobs]
            all_texts = [user_text] + job_texts
            
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
        # Build results with hybrid scores
        results = []
        for i, raw_sim in enumerate(cosine_sim):
            # Text similarity score (0 to 100)
            text_sim_score = max(0.0, min(1.0, float(raw_sim))) * 100.0
            
            # Direct required-to-candidate skills intersection count
            job = jobs[i]
            job_skills_list = [s.strip().lower() for s in (job.skills_required or "").split(",") if s.strip()]
            job_skills_normalized = [normalize_skill(s) for s in job_skills_list if s]
            
            if not job_skills_normalized:
                skills_score = 100.0
            else:
                matched_skills = [s for s in job_skills_normalized if s in candidate_skills_normalized]
                skills_score = (len(matched_skills) / len(job_skills_normalized)) * 100.0
            
            # Hybrid score: 40% text similarity, 60% skills intersection
            hybrid_score = 0.4 * text_sim_score + 0.6 * skills_score
            
            # Apply penalty multiplier (0.2) if the candidate has zero of the required skills
            if len(job_skills_normalized) > 0 and skills_score == 0:
                hybrid_score *= 0.2
                
            final_score = round(max(0.0, min(100.0, hybrid_score)), 2)
            
            results.append({
                'job_id': job.id,
                'score': final_score,
                'job': job
            })
            
        # Sort by score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_n]

class ResumeParser:
    def __init__(self):
        # A basic list of skills to look for. In a real scenario, this would be much more extensive.
        self.common_skills = [
            'python', 'java', 'c++', 'javascript', 'react', 'node.js', 'sql', 'mongodb', 
            'pandas', 'numpy', 'scikit-learn', 'aws', 'docker', 'kubernetes', 'flask', 
            'django', 'html', 'css', 'machine learning', 'deep learning', 'nlp', 'git',
            'project management', 'agile', 'data analysis', 'linux', 'c#', 'php', '.net'
        ]

    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file object."""
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return ""

    def extract_skills(self, text):
        """Extract matching skills from text."""
        text = text.lower()
        found_skills = []
        for skill in self.common_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text):
                found_skills.append(skill)
        return found_skills

    def get_skill_gap(self, user_skills, job_skills):
        """
        user_skills: list of skills
        job_skills: list of required skills
        Returns skills missing in user profile.
        """
        user_skills_set = set([s.lower().strip() for s in user_skills])
        job_skills_set = set([s.lower().strip() for s in job_skills])
        gap = job_skills_set - user_skills_set
        return list(gap)
