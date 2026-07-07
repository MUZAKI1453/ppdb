import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _env_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-this-secret-key')

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///spmb.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.environ.get(
        'UPLOAD_FOLDER',
        os.path.join(BASE_DIR, 'instance', 'uploads')
    )

    # Batas server untuk satu request dibuat longgar karena form berkas
    # dapat mengirim beberapa dokumen sekaligus. Validasi utama tetap per file.
    MAX_CONTENT_LENGTH = _env_int('MAX_REQUEST_CONTENT_LENGTH', 80 * 1024 * 1024)

    # Batas ukuran setiap file upload. Default: 5 MB per file.
    PER_FILE_UPLOAD_LIMIT = _env_int('PER_FILE_UPLOAD_LIMIT', 5 * 1024 * 1024)
    ALLOWED_UPLOAD_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}

    DEBUG = _env_bool('FLASK_DEBUG', False)

    DEFAULT_ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
