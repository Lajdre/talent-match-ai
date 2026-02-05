import asyncio
import logging
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from result import Err

from core import constants
from core.config import config
from core.models.cv_models import CVStructure
from core.utils import extract_text_from_pdf
from repositories.cv_repository import upsert_cv
from services.neo4j_service import get_neo4j_graph
from services.openai_service import get_openai_chat

logger = logging.getLogger(__name__)


async def ingest_cv(path: Path) -> list[dict[str, Any]]:
  """Ingest a CV.

  Accepts a single file or a directory. Non-recursive. Delegates to specific
  processing logic based on the config (USE_LANGCHAIN_LLM_GRAPH_TRANSFORMER).
  """
  path_obj: Path = path.expanduser().resolve()
  if not path_obj.exists():
    raise FileNotFoundError(f"Path not found: {path}")

  if path_obj.is_dir():
    pdf_files = [
      p for p in path_obj.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"
    ]
    if not pdf_files:
      raise ValueError("Directory contains no PDF files")

    results = await asyncio.gather(
      *[_process_single_cv(pdf) for pdf in pdf_files],
      return_exceptions=True,
    )
    return [
      (r if isinstance(r, dict) else {"status": "error", "message": str(r)})
      for r in results
    ]

  if path_obj.suffix.lower() != ".pdf":
    raise ValueError("Provided file is not a PDF")

  return [await _process_single_cv(path_obj)]


async def _process_single_cv(pdf_path: Path) -> dict[str, Any]:
  logger.info("Processing CV: %s", pdf_path.name)

  text_content = extract_text_from_pdf(pdf_path)
  if not text_content.strip():
    return {"status": "warning", "message": f"No text extracted from {pdf_path.name}"}

  if config.USE_LANGCHAIN_LLM_GRAPH_TRANSFORMER:
    return await _ingest_via_transformer(pdf_path, text_content)
  return await _ingest_via_structured_output(pdf_path, text_content)


async def _ingest_via_structured_output(pdf_path: Path, text: str) -> dict[str, Any]:
  """Ingest a CV via structured output."""
  try:
    llm_result = get_openai_chat(temperature=0)
    if isinstance(llm_result, Err):
      assert False  # TODO: propagate further # noqa: B011, PT015, S101, RUF100

    structured_llm = llm_result.ok().with_structured_output(CVStructure)

    prompt = (
      f"Extract the CV information into the structured format.\n"
      f"1. Normalize skill names (e.g., use 'Javascript' instead of 'JS').\n"
      f"2. For proficiency, pick exactly one based on context: Beginner, Intermediate, Advanced, Expert.\n"
      f"3. Do NOT create entries if they don't explicitly exist.\n"
      f"Text:\n{text}"
    )

    result = await structured_llm.ainvoke(prompt)
    cv_data: CVStructure = (
      result if isinstance(result, CVStructure) else CVStructure.model_validate(result)
    )

    upsert_cv(cv_data)

    return {
      "status": "success",
      "method": "structured_output",
      "filename": pdf_path.name,
      "candidate": cv_data.full_name,
      "skills_found": len(cv_data.skills),
    }

  except Exception as e:
    logger.exception("Structured ingestion failed for %s.", pdf_path.name)
    return {"status": "error", "message": str(e)}


async def _ingest_via_transformer(pdf_path: Path, text: str) -> dict[str, Any]:
  """Ingest a CV via LangChain's LLMGraphTransformer, which creates Document nodes."""
  document = Document(
    page_content=text,
    metadata={"source": str(pdf_path), "type": "cv", "filename": pdf_path.name},
  )

  transformer = _get_llm_transformer()
  try:
    graph_documents = await transformer.aconvert_to_graph_documents([document])

    if not graph_documents:
      return {"status": "warning", "message": "LLM failed to extract graph data"}

    graph = get_neo4j_graph()
    graph.add_graph_documents(
      graph_documents,  # type: ignore[arg-type]
      baseEntityLabel=False,
      include_source=False,
    )

    return {
      "status": "success",
      "method": "langchain_transformer",
      "filename": pdf_path.name,
      "nodes_created": len(graph_documents[0].nodes),
      "relationships_created": len(graph_documents[0].relationships),
    }
  except Exception as e:
    logger.exception("LLMGraphTransformer ingestion failed.")
    return {"status": "error", "message": str(e)}


def _get_llm_transformer() -> LLMGraphTransformer:
  """Initialize the LLMGraphTransformer with the specific CV ontology."""
  llm_resulta = get_openai_chat(config.OPENAI_DEFAULT_MODEL)
  if isinstance(llm_resulta, Err):
    assert False  # TODO: propagate further # noqa: B011, PT015, S101, RUF100

  additional_instructions = """
    Ensure skill/technology names use canonical capitalization.
  """

  return LLMGraphTransformer(
    llm=llm_resulta.ok(),
    allowed_nodes=constants.ALLOWED_NODES,
    allowed_relationships=constants.ALLOWED_RELATIONSHIPS,
    node_properties=constants.NODE_PROPERTIES,
    strict_mode=True,
    additional_instructions=additional_instructions,
  )
