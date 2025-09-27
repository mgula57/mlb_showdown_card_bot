import os

class Config:
    # Flask settings
    JSON_SORT_KEYS = False
    
    # File upload settings
    UPLOAD_FOLDER = 'temp_uploads'
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Environment settings
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")

# Create upload directory
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)