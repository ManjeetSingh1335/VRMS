import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "vrms-super-secret-key-mait-cic357-2026")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'vrms.db'}"
    )
    # Ensure postgresql:// scheme compatibility if deployed with older postgres://
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True
    }
    
    # Green Computing / Cache configuration
    GREEN_CACHE_TTL_SECONDS = int(os.getenv("GREEN_CACHE_TTL_SECONDS", 120))
    PAGE_SIZE = int(os.getenv("PAGE_SIZE", 8))
    
    # Rental Business Rules
    LATE_FEE_MULTIPLIER = float(os.getenv("LATE_FEE_MULTIPLIER", 1.5)) # 1.5x daily rate per late day
    CANCELLATION_FEE_PERCENT = float(os.getenv("CANCELLATION_FEE_PERCENT", 10.0)) # 10% cancellation charge
