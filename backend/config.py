from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "hostelos"
    jwt_secret: str = "supersecretjwtkeythatshouldbechangedinproduction"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = "backend/.env"

settings = Settings()
