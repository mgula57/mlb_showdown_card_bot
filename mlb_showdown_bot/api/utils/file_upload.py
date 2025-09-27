import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from config import Config

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def process_uploaded_file(file: FileStorage) -> dict:
    """Process and save the uploaded file"""
    try:
        # Check if file is allowed
        if not allowed_file(file.filename):
            raise Exception(f"File type not allowed: {file.filename}")
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        
        return {
            'filename': unique_filename,
            'path': file_path,
            'original_name': filename
        }
        
    except Exception as e:
        raise Exception(f"Error processing uploaded file: {str(e)}")

def cleanup_uploaded_file(uploaded_file_info):
    """Clean up uploaded file"""
    if uploaded_file_info and os.path.exists(uploaded_file_info['path']):
        os.remove(uploaded_file_info['path'])