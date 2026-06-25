from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///pygrow.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    coze_bot_id: str = ""
    coze_token: str = ""

    # AI / LLM
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model_name: str = "gpt-3.5-turbo"

    # ASR (Speech Recognition)
    asr_provider: str = "mock"  # mock / aliyun / whisper
    aliyun_asr_access_key_id: str = ""
    aliyun_asr_access_key_secret: str = ""
    aliyun_asr_app_key: str = ""
    asr_whisper_model: str = "base"  # tiny / base / small / medium / large

    # Bilibili
    bilibili_cookie: str = ""
    bilibili_cookie_file: str = ""

    # DeepSeek
    deepseek_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}


settings = Settings()
