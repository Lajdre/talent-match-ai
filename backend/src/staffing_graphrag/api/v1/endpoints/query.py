from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import query_service

router = APIRouter(prefix="/query")


class QueryRequest(BaseModel):
  question: str


class QueryResponse(BaseModel):
  question: str
  answer: str
  cypher_query: str = ""
  success: bool
  error: str | None = None


@router.post("/", response_model=QueryResponse)
async def query_knowledge_graph(request: QueryRequest) -> dict[str, Any]:
  """Ask a natural language question to the Knowledge Graph."""
  if not request.question.strip():
    raise HTTPException(status_code=400, detail="Question cannot be empty")

  return await query_service.process_query(request.question)


@router.get("/examples", response_model=dict[str, list[str]])
async def get_example_queries() -> dict[str, list[str]]:
  """Get a list of suggested queries to help the user."""
  return query_service.get_example_queries_list()
