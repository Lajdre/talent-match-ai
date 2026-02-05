from typing import Any

from fastapi import APIRouter, HTTPException, Query
from shared_types.matching_types import MatchResponse
from shared_types.project_types import ProjectAssignmentRequest

from repositories.matching_repository import MatchingRepository

router = APIRouter(prefix="/match")
repo = MatchingRepository()


@router.get("/{rfp_id}", response_model=MatchResponse)
async def find_matches(
  rfp_id: str,
  threshold_months: int = Query(1, description="Months to consider 'Available Soon'"),
) -> MatchResponse:
  """Run the matching algorithm for a specific RFP.

  Returns candidates categorized by:
  1. Perfect Matches (Skills + Available Now)
  2. Future Matches (Skills + Available within X months)
  3. Partial Matches (Available but missing mandatory skills)
  """
  try:
    return repo.find_candidates(rfp_id, threshold_months)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/{rfp_id}/confirm")
async def confirm_assignment(
  rfp_id: str, request: ProjectAssignmentRequest
) -> dict[str, Any]:
  """Finalize the RFP.

  1. Converts RFP to a Project.
  2. Assigns the selected programmers.
  3. Deletes the RFP from search.
  """
  try:
    new_project_id = repo.convert_rfp_to_project(rfp_id, request.programmer_ids)
    return {
      "status": "success",
      "message": "Project created successfully",
      "project_id": new_project_id,
      "rfp_id": rfp_id,
    }
  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e)) from None
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e)) from None
