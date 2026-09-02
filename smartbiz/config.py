import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "smartbiz-hackathon-super-secret-key-2026")
    
    # Database
    DATABASE_DIR = BASE_DIR / "database"
    DATABASE_DIR.mkdir(exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{DATABASE_DIR / 'smartbiz.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    SAMPLES_FOLDER = UPLOAD_FOLDER / "samples"
    SAMPLES_FOLDER.mkdir(exist_ok=True)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file upload
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "png", "jpg", "jpeg"}
    
    # AI Service Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Business Automation Confidence Thresholds (0 - 100)
    AUTO_PROCESS_THRESHOLD = int(os.getenv("AUTO_PROCESS_THRESHOLD", "80"))
    HITL_REVIEW_THRESHOLD = int(os.getenv("HITL_REVIEW_THRESHOLD", "60"))
    
    # Departments
    DEPARTMENTS = ["Finance", "Sales", "HR", "Support", "Admin", "Marketing"]
    ROLES = ["admin", "finance", "sales", "hr", "support"]
