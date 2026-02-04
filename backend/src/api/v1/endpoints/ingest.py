import logging
import tempfile
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from services.ingest_cv import ingest_cv
from services.ingest_projects import process_projects_json
from services.ingest_rfp import ingest_rfp

router = APIRouter(prefix="/ingest")

logger = logging.getLogger(__name__)


class IngestRequest(BaseModel):
  file_path: str


# --- File path endpoints ---


@router.post("/cv")
async def ingest_cv_endpoint(request: IngestRequest) -> dict:
  """Ingest a single CV PDF or every PDF inside a directory (non-recursive)."""
  try:
    results: list[dict] = await ingest_cv(Path(request.file_path))
    return results[0]  # TODO: handle multiple retrun values
  except FileNotFoundError:
    raise HTTPException(
      status_code=404, detail="CV file or directory not found"
    ) from None
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e)) from None
  except Exception:
    logger.exception("CV ingestion error.")
    raise HTTPException(status_code=500, detail="Internal processing error") from None


@router.post("/rfp")
async def ingest_rfp_endpoint(request: IngestRequest) -> dict:
  """Ingest a single RFP PDF or every RFP PDF inside a directory."""
  try:
    results: list[dict] = await ingest_rfp(Path(request.file_path))
    return results[0]  # TODO: handle multiple retrun values
  except FileNotFoundError:
    raise HTTPException(
      status_code=404, detail="RFP file or directory not found"
    ) from None
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e)) from None
  except Exception:
    logger.exception("RFP ingestion error.")
    raise HTTPException(status_code=500, detail="Internal processing error") from None


@router.post("/projects")
async def ingest_projects_endpoint(request: IngestRequest) -> dict:
  """Trigger the ingestion of the projects file into Neo4j.

  This parses the file and creates Project nodes, Requirement links, and Assignments.
  """
  try:
    return await process_projects_json(Path(request.file_path))
  except FileNotFoundError:
    raise HTTPException(status_code=404, detail="File not found") from None
  except Exception as e:
    logger.exception("Project ingestion error")
    raise HTTPException(status_code=500, detail=str(e)) from None


# --- File upload endpoints ---


@router.post("/cv/upload")
async def ingest_cv_upload(
  file: Annotated[UploadFile, File(...)],
) -> list[dict[str, Any]]:
  """Upload and ingest a CV PDF."""
  if not (file.filename and file.filename.lower().endswith(".pdf")):
    raise HTTPException(status_code=400, detail="File must be a PDF")

  tmp_path: Path | None = None
  try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
      content = await file.read()
      tmp.write(content)
      tmp_path = Path(tmp.name)

    return await ingest_cv(tmp_path)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e)) from None
  except Exception:
    logger.exception("CV upload ingestion error.")
    raise HTTPException(status_code=500, detail="Internal processing error") from None
  finally:
    if tmp_path:
      Path(tmp_path).unlink(missing_ok=True)


@router.post("/rfp/upload", status_code=status.HTTP_201_CREATED)
async def ingest_rfp_upload(
  file: Annotated[UploadFile, File(description="RFP PDF document")],
) -> dict[str, str]:
  """Upload and ingest an RFP PDF."""
  if not file.filename or not file.filename.lower().endswith(".pdf"):
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="File must be a PDF",
    )

  tmp_path: Path | None = None
  try:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
      content = await file.read()
      tmp.write(content)
      tmp_path = Path(tmp.name)

    await ingest_rfp(tmp_path)
    return {
      "message": "RFP ingested successfully",
      "filename": file.filename,
    }

  except ValueError as e:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
    ) from None
  except Exception:
    logger.exception("RFP upload ingestion failed.")
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Internal processing error",
    ) from None
  finally:
    if tmp_path and tmp_path.exists():
      tmp_path.unlink(missing_ok=True)


@router.post("/projects/upload")
async def ingest_projects_upload(
  file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
  """Upload and ingest a projects JSON file."""
  if not (file.filename and file.filename.lower().endswith(".json")):
    raise HTTPException(status_code=400, detail="File must be a JSON file")

  tmp_path: str | None = None
  try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
      content = await file.read()
      tmp.write(content)
      tmp_path = tmp.name

    return await process_projects_json(Path(tmp_path))
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e)) from None
  except Exception as e:
    logger.exception("Projects upload ingestion error.")
    raise HTTPException(status_code=500, detail=str(e)) from None
  finally:
    if tmp_path:
      Path(tmp_path).unlink(missing_ok=True)
