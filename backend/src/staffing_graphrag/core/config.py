from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
  PROJECT_NAME: str = "Talent Match AI"
  API_VERSION: str = "0.1.0"
  API_V1_STR: str = "/api/v1"

  SERVER_HOST: str = "127.0.0.1"
  SERVER_PORT: int = 8032
  SERVER_DEBUG_MODE: bool = True

  NEO4J_URI: str = "bolt://localhost:7687"
  NEO4J_USERNAME: str = "neo4j"
  NEO4J_PASSWORD: SecretStr | None = None

  OPENAI_API_KEY: SecretStr | None = None
  OPENAI_DEFAULT_MODEL: str = "gpt-4o-mini"
  OPENAI_DEFAULT_TEMPERATURE: float = 0
  OPENAI_GRAPH_QUERY_MODEL: str = "gpt-4o"

  USE_LANGCHAIN_LLM_GRAPH_TRANSFORMER: bool = False

  model_config = SettingsConfigDict(env_file=".env", extra="ignore")

  @field_validator("NEO4J_PASSWORD")
  @classmethod
  def password_not_empty(cls, neo4j_password: SecretStr | None) -> SecretStr:
    if not (neo4j_password and neo4j_password.get_secret_value().strip()):
      raise ValueError("NEO4J_PASSWORD cannot be empty")
    return neo4j_password

  @field_validator("OPENAI_API_KEY")
  @classmethod
  def openai_api_key_not_empty(cls, openai_api_key: SecretStr | None) -> SecretStr:
    if not (openai_api_key and openai_api_key.get_secret_value().strip()):
      raise ValueError("OPENAI_API_KEY cannot be empty")
    return openai_api_key


config = Config()
