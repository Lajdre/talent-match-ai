import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
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
async def ingest_cv_endpoint(request: IngestRequest):
  """
  Ingest a single CV PDF or every PDF inside a directory (non-recursive).
  """
  try:
    results: list[dict] = await ingest_cv(request.file_path)
    return results[0]  # for now
    # return results if len(results) != 1 else results[0]   # backward compat
  except FileNotFoundError:
    raise HTTPException(status_code=404, detail="CV file or directory not found")
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logger.error("CV ingestion error: %s", e)
    raise HTTPException(status_code=500, detail="Internal processing error")


@router.post("/rfp")
async def ingest_rfp_endpoint(request: IngestRequest):
  """
  Ingest a single RFP PDF or every PDF inside a directory.
  """
  try:
    results: list[dict] = await ingest_rfp(request.file_path)
    # return results if len(results) != 1 else results[0]
    return results[0]  # for now
  except FileNotFoundError:
    raise HTTPException(status_code=404, detail="RFP file or directory not found")
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logger.error("RFP Ingestion error: %s", e)
    raise HTTPException(status_code=500, detail="Internal processing error")


@router.post("/projects")
async def ingest_projects_endpoint(request: IngestRequest):
  """
  Trigger the ingestion of the projects file into Neo4j.
  This parses the file and creates Project nodes, Requirement links, and Assignments.
  """
  try:
    result = await process_projects_json(Path(request.file_path))
    return result
  except FileNotFoundError:
    raise HTTPException(status_code=404, detail="File not found")
  except Exception as e:
    logger.error(f"Project ingestion error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))


# --- File upload endpoints ---


@router.post("/cv/upload")
async def ingest_cv_upload(file: UploadFile = File(...)):
  """Upload and ingest a CV PDF."""
  if not (file.filename and file.filename.lower().endswith(".pdf")):
    raise HTTPException(status_code=400, detail="File must be a PDF")

  tmp_path: str | None = None
  try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
      content = await file.read()
      tmp.write(content)
      tmp_path = tmp.name

    result = await ingest_cv(tmp_path)
    return result
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logger.error(f"CV upload ingestion error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal processing error")
  finally:
    if tmp_path:
      Path(tmp_path).unlink(missing_ok=True)


@router.post("/rfp/upload")
async def ingest_rfp_upload(file: UploadFile = File(...)):
  """Upload and ingest an RFP PDF."""
  if not (file.filename and file.filename.lower().endswith(".pdf")):
    raise HTTPException(status_code=400, detail="File must be a PDF")

  tmp_path: str | None = None
  try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
      content = await file.read()
      tmp.write(content)
      tmp_path = tmp.name

    result = await ingest_rfp(tmp_path)
    return result
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logger.error(f"RFP upload ingestion error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal processing error")
  finally:
    if tmp_path:
      Path(tmp_path).unlink(missing_ok=True)


@router.post("/projects/upload")
async def ingest_projects_upload(file: UploadFile = File(...)):
  """Upload and ingest a projects JSON file."""
  if not (file.filename and file.filename.lower().endswith(".json")):
    raise HTTPException(status_code=400, detail="File must be a JSON file")

  tmp_path: str | None = None
  try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
      content = await file.read()
      tmp.write(content)
      tmp_path = tmp.name

    result = await process_projects_json(Path(tmp_path))
    return result
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logger.error(f"Projects upload ingestion error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
  finally:
    if tmp_path:
      Path(tmp_path).unlink(missing_ok=True)
