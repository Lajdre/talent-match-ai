from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from core.models import ProgrammerRead, ProjectRead, RFPRead
from repositories import programmer_repository, project_repository, rfp_repository

router = APIRouter(prefix="/entities")


@router.get("/programmers", response_model=list[ProgrammerRead])
async def get_programmers(
  status: Literal["available", "assigned"] | None = Query(
    None, description="Filter by assignment status"
  ),
):
  """
  Get all programmers.
  Use ?status=available to find people ready for new projects.
  """
  try:
    return programmer_repository.get_programmers(status)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects", response_model=list[ProjectRead])
async def get_projects():
  """
  Get all projects (historical and active) with their team and tech stack.
  """
  try:
    return project_repository.get_projects()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/rfps", response_model=list[RFPRead])
async def get_rfps():
  """
  Get all active RFPs and their specific skill requirements.
  """
  try:
    return rfp_repository.get_rfps()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
