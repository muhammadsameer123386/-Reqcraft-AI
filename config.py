"""
ReqCraft AI - Configuration
Loads settings from environment variables (.env file).
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'reqcraft.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===== LLM Providers (Smart Fallback Chain) =====
    # 1. Gemini (Primary)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # 2. HuggingFace (Fallback)
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

    # 3. Ollama (Local Backup)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
