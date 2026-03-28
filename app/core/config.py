import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # JWT 秘钥
    SECRET_KEY: str = "default-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    
    DATABASE_NAME: str = "default_db"
    DATABASE_USER: str = "default_user"
    DATABASE_PASSWORD: str = "default_password"
    DATABASE_DOMAIN: str = "localhost"
    DATABASE_PORT: str = "3306"

    # 用 property 动态拼接 URL
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_DOMAIN}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    # AI 接口配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

