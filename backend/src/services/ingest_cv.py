import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer

from core import constants
from core.utils import extract_text_from_pdf
from services.neo4j_service import get_neo4j_graph
from services.openai_service import get_openai_chat

logger = logging.getLogger(__name__)


async def process_cv_pdf(file_path: str) -> dict:
  """Pipeline: PDF -> Text -> Graph Documents (using LLM) -> Stores in Neo4j"""
  cv_path = Path(file_path)
  if not cv_path.exists():
    raise FileNotFoundError(f"File not found: {file_path}")

  logger.info(f"Processing CV: {cv_path.name}")

  text_content = extract_text_from_pdf(cv_path)
  if not text_content.strip():
    return {"status": "warning", "message": "No text extracted from PDF"}

  document = Document(
    page_content=text_content,
    metadata={"source": str(cv_path), "type": "cv", "filename": cv_path.name},
  )

  try:
    transformer: LLMGraphTransformer = _get_llm_transformer()
    graph_documents: list = await transformer.aconvert_to_graph_documents([document])

    if not graph_documents:
      return {"status": "warning", "message": "LLM failed to extract graph data"}

    nodes_count = len(graph_documents[0].nodes)
    rels_count = len(graph_documents[0].relationships)

    logger.info(f"Extracted {nodes_count} nodes and {rels_count} relationships")

  except Exception as e:
    logger.error(f"LLM Transformation failed: {e}")
    raise RuntimeError(f"Graph transformation failed: {str(e)}")

  try:
    graph = get_neo4j_graph()
    graph.add_graph_documents(
      graph_documents,
      baseEntityLabel=True,  # Adds __Entity__ label for indexing
      include_source=True,  # Good for RAG references
    )
  except Exception as e:
    logger.error(f"Neo4j storage failed: {e}")
    raise RuntimeError(f"Database storage failed: {str(e)}")

  return {
    "status": "success",
    "filename": cv_path.name,
    "nodes_created": nodes_count,
    "relationships_created": rels_count,
  }


def _get_llm_transformer() -> LLMGraphTransformer:
  """
  Initializes the LLMGraphTransformer with the specific CV ontology.
  """
  openai_chat_resulta = get_openai_chat(constants.OPENAI_MODEL)
  if openai_chat_resulta.err():
    raise  # TODO: propagate further

  return LLMGraphTransformer(
    llm=openai_chat_resulta.unwrap(),
    allowed_nodes=constants.ALLOWED_NODES,
    allowed_relationships=constants.ALLOWED_RELATIONSHIPS,
    node_properties=constants.NODE_PROPERTIES,
    strict_mode=True,
  )
