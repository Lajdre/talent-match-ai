from fastapi import FastAPI

from api.v1.master_router import router
from core.config import config

app = FastAPI(
  title=config.PROJECT_NAME,
  version=config.API_VERSION,
  openapi_url=f"{config.API_V1_STR}/openapi.json",
)

app.include_router(router)


if __name__ == "__main__":
  import uvicorn

  uvicorn.run(
    "src.main:app",
    host=config.SERVER_HOST,
    port=config.SERVER_PORT,
    reload=config.SERVER_DEBUG_MODE,
  )
