from typing import Any

from fastapi import APIRouter, HTTPException, Query

from repositories import system_repository

router = APIRouter(prefix="/info")


@router.get("/stats", response_model=dict[str, Any])
async def get_graph_statistics():
  """
  Retrieve statistics, schema information, and health status of the Knowledge Graph.
  """
  data = system_repository.get_graph_metadata()
  if "error" in data:
    raise HTTPException(status_code=500, detail=data["error"])
  return data


@router.get("/sample", response_model=list[dict[str, Any]])
async def get_node_samples(
  label: str = Query(..., description="The node label to sample, e.g., 'Person'"),
):
  """
  Get a few raw records for a specific node label to inspect data quality.
  """
  samples = system_repository.get_node_sample(label)
  return samples
