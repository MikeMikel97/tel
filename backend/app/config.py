"""Конфигурация приложения"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://telephony_user:telephony_password_2024@localhost:5432/telephony"
    
    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    
    # OpenRouter API
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Soniox API
    soniox_api_key: str = ""
    
    # Asterisk ARI
    asterisk_host: str = "127.0.0.1"
    asterisk_ari_port: int = 8088
    asterisk_ari_user: str = "ai-agent"
    asterisk_ari_password: str = "aiagent_secret_password_2024"
    
    # Asterisk Config
    asterisk_config_path: str = "/etc/asterisk"
    
    # Пути
    recordings_path: str = "/var/spool/asterisk/recording"
    
    # Сервер
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # LLM настройки
    llm_model: str = "anthropic/claude-3.5-sonnet"  # или "openai/gpt-4o-mini"
    llm_temperature: float = 0.3
    
    # STT настройки
    soniox_model: str = "ru"  # Русская модель
    soniox_sample_rate: int = 16000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Global settings instance
settings = get_settings()
