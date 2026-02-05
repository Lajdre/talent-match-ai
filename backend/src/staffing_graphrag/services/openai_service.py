from functools import lru_cache

from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from result import Err, Ok, Result

from core.config import config


@lru_cache(maxsize=1)
def get_openai_chat(
  model_name: str = config.OPENAI_DEFAULT_MODEL,
  temperature: float = config.OPENAI_DEFAULT_TEMPERATURE,
) -> Result[ChatOpenAI, str]:
  if not config.OPENAI_API_KEY:
    return Err("OpenAI api key is missing.")

  return Ok(
    ChatOpenAI(
      model=model_name,
      temperature=temperature,
      api_key=SecretStr(config.OPENAI_API_KEY.get_secret_value()),
    )
  )
