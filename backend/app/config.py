from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./grader.db"
    redis_url: str = ""
    mongo_url: str | None = None
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    upload_dir: str = "./uploads"
    openai_base_url: str = "https://api.nova.amazon.com/v1/chat/completions"
    model_config = {"env_file": ".env"}


settings = Settings()
