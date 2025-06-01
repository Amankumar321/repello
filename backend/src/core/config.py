from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    GOOGLE_SEARCH_ENGINE_ID: str
    HUGGINGFACE_TOKEN: str
    
    # Service Configuration
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=ENVIRONMENT == "development", env="DEBUG")
    PORT: int = Field(default=8000, env="PORT")
    
    # Search Configuration
    DEFAULT_SEARCH_RESULTS: int = 5
    MAX_SEARCH_RESULTS: int = 10
    MAX_SEARCH_DEPTH: int = 3  # Maximum number of search iterations
    
    # Security Configuration
    PROMPT_INJECTION_THRESHOLD: float = 0.8
    BAN_TOPICS_THRESHOLD: float = 0.6
    
    # LLM Configuration
    LLM_MODEL: str = "gpt-4.1-nano"
    LLM_TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 4000
    
    # API Configuration
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Cache Configuration
    CACHE_TTL: int = 3600  # 1 hour in seconds
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache to avoid reading .env file for every request
    """
    return Settings() 