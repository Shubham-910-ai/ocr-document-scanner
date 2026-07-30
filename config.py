import os
import shutil

# Base Directory of the Application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application Configuration Settings"""
    
    # Secret Key for Flask-WTF CSRF and Sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-ocr-scanner-key-2026'
    
    # Upload and File Processing Directories
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PROCESSED_FOLDER = os.path.join(BASE_DIR, 'processed')
    DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
    TESSDATA_DIR = os.path.join(BASE_DIR, 'tessdata')
    
    # Security Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'pdf'}
    
    # Supported OCR Languages (including Multilingual Eng+Hin)
    SUPPORTED_LANGUAGES = {
        'eng+hin': 'English + Hindi (Bilingual / द्विभाषी)',
        'eng': 'English',
        'hin': 'Hindi (हिन्दी)',
        'spa': 'Spanish',
        'fra': 'French',
        'deu': 'German',
        'ita': 'Italian',
        'por': 'Portuguese',
        'rus': 'Russian',
        'chi_sim': 'Chinese (Simplified)'
    }
    DEFAULT_LANGUAGE = 'eng+hin'
    
    # Tesseract OCR Path Auto-Detection
    @staticmethod
    def get_tesseract_cmd():
        """Auto-detect Tesseract OCR binary path across Windows, Linux, and macOS."""
        # 1. Check explicit environment variable
        env_cmd = os.environ.get('TESSERACT_CMD')
        if env_cmd and os.path.isfile(env_cmd):
            return env_cmd
            
        # 2. Check standard Windows installation locations
        windows_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe')
        ]
        for wpath in windows_paths:
            if os.path.isfile(wpath):
                return wpath
                
        # 3. Check system PATH via shutil.which
        which_tesseract = shutil.which('tesseract')
        if which_tesseract:
            return which_tesseract
            
        # 4. Standard Unix paths
        unix_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract'
        ]
        for upath in unix_paths:
            if os.path.isfile(upath):
                return upath
                
        return None

TESSERACT_CMD = Config.get_tesseract_cmd()
