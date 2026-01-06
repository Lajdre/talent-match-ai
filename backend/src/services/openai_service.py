from functools import lru_cache

from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from result import Err, Ok, Result

from core import constants
from core.config import config


@lru_cache(maxsize=1)
def get_openai_chat(
  model_name: str = constants.OPENAI_MODEL, temperature: float = 0
) -> Result[ChatOpenAI, str]:
  api_key = config.OPENAI_API_KEY
  if not api_key:
    return Err("OpenAI api key is missing.")

  return Ok(
    ChatOpenAI(
      model=model_name,
      temperature=temperature,
      api_key=SecretStr(config.OPENAI_API_KEY),
    )
  )
