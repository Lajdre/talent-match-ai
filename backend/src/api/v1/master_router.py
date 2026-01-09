from fastapi import APIRouter

from api.v1.endpoints.admin import router as admin_router
from api.v1.endpoints.entities import router as entities_router
from api.v1.endpoints.info import router as info_router
from api.v1.endpoints.ingest import router as ingest_router
from api.v1.endpoints.matching import router as matching_router
from api.v1.endpoints.query import router as query_router
from core.config import config

rounter = APIRouter(prefix=config.API_V1_STR)

rounter.include_router(entities_router, tags=["Get Entities Operations"])
rounter.include_router(info_router, tags=["Info Operations"])
rounter.include_router(ingest_router, tags=["Ingest Operations"])
rounter.include_router(matching_router, tags=["Matching Operations"])
rounter.include_router(query_router, tags=["Query Operations"])
rounter.include_router(admin_router, tags=["Admin Operations"])
