import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'f1-analytics-secret-key-2025')
    
    # MySQL Database
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'f1_analytics')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # FastF1 Cache
    FASTF1_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'f1_cache')
    
    # Seasons to load
    HISTORICAL_SEASONS = [2025]
    LIVE_SEASON = 2026
