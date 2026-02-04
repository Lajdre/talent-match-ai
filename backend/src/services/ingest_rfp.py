import asyncio
import json
import logging
from pathlib import Path

from result import Err

from core.constants import RFP_JSON_FILE, RFP_STORAGE_DIR
from core.models.rfp_models import RFPStructure
from core.utils import extract_text_from_pdf
from repositories.rfp_repository import get_next_rfp_id, save_rfp
from services.openai_service import get_openai_chat

logger = logging.getLogger(__name__)


async def _extract_rfp_data(text: str) -> RFPStructure:
  """Use OpenAI Structured Output to parse raw text into the RFP Pydantic model."""
  openai_chat_result = get_openai_chat(temperature=0)
  if isinstance(openai_chat_result, Err):
    assert False  # TODO: propagate further # noqa: B011, PT015

  structured_llm = openai_chat_result.ok().with_structured_output(RFPStructure)

  try:
    result = await structured_llm.ainvoke(
      f"Extract the following RFP information from the text provided. "
      "Important: If you see skills like PostgreSQL or JavaScript, that shuld be included in the output, they should be written like 'Postgresql' and 'Javascript' - in the final version. "
      "Other formatting should be standard. "
      f"Infer missing dates or details logically if implied.\n\nText:\n{text}"
    )
    if isinstance(result, RFPStructure):
      return result
    return RFPStructure.model_validate(result)
  except Exception:
    logger.exception("LLM Extraction failed")
    raise ValueError("Failed to parse RFP structure from text") from None


def _save_to_json_file(rfp_data: RFPStructure) -> None:
  """Upsert and RFP to the global rfps.json file.

  Handles the file creation if the file doesn't exist.
  """
  if not RFP_STORAGE_DIR.exists():
    RFP_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

  current_data = []

  if RFP_JSON_FILE.exists():
    try:
      with RFP_JSON_FILE.open("r") as f:
        current_data = json.load(f)
    except json.JSONDecodeError:
      logger.exception("rfps.json was corrupted, starting fresh.")
      current_data = []

  rfp_dict = rfp_data.model_dump()

  updated = False
  for i, item in enumerate(current_data):
    if item.get("id") == rfp_dict["id"]:
      current_data[i] = rfp_dict
      updated = True
      break

  if not updated:
    current_data.append(rfp_dict)

  with RFP_JSON_FILE.open("w") as f:
    json.dump(current_data, f, indent=2)


async def _process_rfp(pdf_path: Path) -> dict:
  logger.info("Processing RFP: %s", pdf_path.name)

  text_content = extract_text_from_pdf(pdf_path)
  if not text_content.strip():
    return {"status": "error", "message": f"No text extracted from {pdf_path.name}"}

  rfp_structure = await _extract_rfp_data(text_content)
  rfp_structure.id = get_next_rfp_id()
  _save_to_json_file(rfp_structure)

  try:
    save_rfp(rfp_structure)
  except Exception:
    logger.exception("Neo4j ingestion failed.")
    return {
      "status": "partial_success",
      "message": "Saved to JSON but failed to sync to Graph",
      "data": rfp_structure.model_dump(),
    }

  return {
    "status": "success",
    "message": f"RFP {rfp_structure.id} processed successfully",
    "data": rfp_structure.model_dump(),
  }


async def ingest_rfp(path: Path) -> list[dict]:
  """Ingest an RFP: PDF -> Text -> Pydantic -> JSON and Neo4j."""
  if not path.exists():
    raise FileNotFoundError(f"File not found: {path}")

  if path.is_dir():
    pdf_files = sorted(path.glob("*.pdf"))
    if not pdf_files:
      raise ValueError("Directory contains no PDF files")

    results = await asyncio.gather(
      *[_process_rfp(pdf) for pdf in pdf_files],
      return_exceptions=True,
    )

    return [
      (r if isinstance(r, dict) else {"status": "error", "message": str(r)})
      for r in results
    ]

  if not path.suffix.lower() == ".pdf":
    raise ValueError("Provided file is not a PDF")

  return [await _process_rfp(path)]
