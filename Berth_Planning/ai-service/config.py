"""
SmartBerth AI Service - Configuration
Manages settings for LLM model and database connections
Uses Perplexity Sonar API for cloud-based AI inference
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Anthropic Claude API Settings
    # NOTE: Set via environment variable or .env file (ANTHROPIC_API_KEY)
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")
    claude_model: str = "claude-opus-4-20250514"  # Claude Opus 4 - most capable model
    
    # Legacy Ollama settings (kept for fallback)
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "smartberth-qwen3"
    
    # Context and Generation Settings
    n_ctx: int = 200000  # Claude's context window size
    max_new_tokens: int = 2048  # Increased for Claude
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8001  # Changed to 8001 to avoid conflicts
    
    # Database Connection (LocalDB for development/demo)
    db_server: str = "(localdb)\\MSSQLLocalDB"
    db_name: str = "BerthPlanning"
    db_user: str = ""
    db_password: str = ""
    db_trusted_connection: str = "yes"
    
    # RAG Settings
    chroma_persist_dir: str = "./chroma_db_new"  # Updated to new ChromaDB folder
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50    # Weather API Settings (WeatherAPI.com)
    
    weather_api_provider: str = "WeatherAPI"
    weather_api_key: str = "4ea0cae40cd5439ca6d203714260502"  # WeatherAPI.com free tier
    weather_cache_duration_hours: int = 1
    weather_proximity_threshold_nm: float = 10.0  # Nautical miles for spatial caching
   
    
    # Logging
    log_level: str = "INFO"
    
    @property
    def db_connection_string(self) -> str:
        """Generate ODBC connection string for SQL Server"""
        if self.db_trusted_connection.lower() == "yes":
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.db_server};"
                f"DATABASE={self.db_name};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )
        else:
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.db_server};"
                f"DATABASE={self.db_name};"
                f"UID={self.db_user};"
                f"PWD={self.db_password};"
                f"TrustServerCertificate=yes;"
            )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Base directory for the AI service
BASE_DIR = Path(__file__).resolve().parent

# Knowledge base documents directory
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"

# Ensure directories exist
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)
