from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./grader.db"
    redis_url: str = "redis://default:ODE5781XSFzPoDyOp28ZDCJPHgPchmJD@handsome-support-activity-33852.db.redis.io:14415"

    mongo_url: str | None = None
    openai_api_key: str = "v1.CmMKHHN0YXRpY2tlS1lMDB5aHIweHFhcGozOGJwd3oSIXNlcnZpY2VhY2NvdW50LWUwMHEwYWpnNzNjMjhreDBzNjIMCOT3ndYGEMSRwvsBOgsI4vq1oQcQgISvX0ACWgNlMDA.AAAAAAAAAAFX_T_fl1bYFyay_9RL-mn_vfDQRY0LZZfPqwFzk2EyHE49-nUJlY0HTxK1ZlqcS02jL8pCXRA5bYrzUHoD5pAK"
    openai_model: str = "moonshotai/Kimi-K2.6"
    upload_dir: str = "./uploads"
    openai_base_url: str = "https://api.tokenfactory.us-central1.nebius.com/v1/"
    model_config = {"env_file": ".env"}

settings = Settings()
