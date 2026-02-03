import logging

from fastapi import APIRouter, HTTPException, status

from services.admin_service import reset_database

router = APIRouter(prefix="/admin")
logger = logging.getLogger(__name__)


@router.delete("/db/reset", status_code=status.HTTP_200_OK)
async def reset_db_endpoint() -> dict:
  """
  DANGER: Completely wipes the Neo4j database.
  Deletes all nodes, relationships, indexes, and constraints.
  Use only for development/testing.
  """
  try:
    result = reset_database()
    return result
  except Exception as e:
    logger.error(f"Reset failed: {e}")
    raise HTTPException(
      status_code=500,
      detail="Failed to reset database",
    ) from None
