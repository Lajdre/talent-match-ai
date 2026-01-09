from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
  PROJECT_NAME: str = "Talent Match AI"
  API_VERSION: str = "0.1.0"
  API_V1_STR: str = "/api/v1"

  SERVER_HOST: str = "0.0.0.0"
  SERVER_PORT: int = 8032
  SERVER_DEBUG_MODE: bool = True

  NEO4J_URI: str = "bolt://localhost:7687"
  NEO4J_USERNAME: str = "neo4j"
  NEO4J_PASSWORD: str = "password"

  OPENAI_API_KEY: str = ""

  model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = Config()
