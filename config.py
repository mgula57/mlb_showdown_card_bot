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

    # Admin allowlist — Supabase user ids (and/or emails) that may publish curated teams and
    # manage collections. Comma-separated in the env; compared case-insensitively for emails.
    ADMIN_USER_IDS = {
        v.strip() for v in os.environ.get("ADMIN_USER_IDS", "").split(",") if v.strip()
    }
    ADMIN_EMAILS = {
        v.strip().lower() for v in os.environ.get("ADMIN_EMAILS", "").split(",") if v.strip()
    }

# Create upload directory
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)