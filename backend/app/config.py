from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./grader.db"
    redis_url: str = "redis://default:gQAAAAAAAx36AAIgcDFjMmM4ODBhZjg4OTE0ZWE2OTljZDQ3MDE5OGExYWRlZA@awake-perch-204282.upstash.io:6379"
    mongo_url: str | None = None
    openai_api_key: str = "b73cea7d-c155-4158-b1fa-9e6bf817e6f1"
    openai_model: str = "gpt-4o"
    upload_dir: str = "./uploads"
    openai_base_url: str = "https://api.nova.amazon.com/v1/chat/completions"
    model_config = {"env_file": ".env"}


settings = Settings()
