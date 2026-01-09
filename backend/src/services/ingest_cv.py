import asyncio
import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer

from core import constants
from core.utils import extract_text_from_pdf
from services.neo4j_service import get_neo4j_graph
from services.openai_service import get_openai_chat

logger = logging.getLogger(__name__)


async def _process_single_cv(pdf_path: Path) -> dict:
  logger.info("Processing CV: %s", pdf_path.name)

  text_content = extract_text_from_pdf(pdf_path)
  if not text_content.strip():
    return {"status": "warning", "message": f"No text extracted from {pdf_path.name}"}

  document = Document(
    page_content=text_content,
    metadata={"source": str(pdf_path), "type": "cv", "filename": pdf_path.name},
  )

  transformer = _get_llm_transformer()
  graph_documents = await transformer.aconvert_to_graph_documents([document])

  if not graph_documents:
    return {
      "status": "warning",
      "message": f"LLM failed to extract graph data for {pdf_path.name}",
    }

  nodes_count = len(graph_documents[0].nodes)
  rels_count = len(graph_documents[0].relationships)

  graph = get_neo4j_graph()
  graph.add_graph_documents(
    graph_documents,  # type: ignore[arg-type]
    baseEntityLabel=False,
    include_source=False,
  )

  return {
    "status": "success",
    "filename": pdf_path.name,
    "nodes_created": nodes_count,
    "relationships_created": rels_count,
  }


# async def ingest_cv(file_path: str) -> dict:
async def ingest_cv(file_path: str) -> list[dict]:
  """
  Accepts a single PDF file or a directory.
  Returns a list of result dicts (one per PDF).  Non-recursive.
  """
  path_obj = Path(file_path).expanduser().resolve()
  if not path_obj.exists():
    raise FileNotFoundError(f"Path not found: {file_path}")

  # ----- directory branch -----
  if path_obj.is_dir():
    pdf_files = [
      p for p in path_obj.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"
    ]
    if not pdf_files:
      raise ValueError("Directory contains no PDF files")
    # run all CVs concurrently
    results = await asyncio.gather(
      *[_process_single_cv(pdf) for pdf in pdf_files],
      return_exceptions=True,
    )
    # convert exceptions to error dicts
    return [
      (r if isinstance(r, dict) else {"status": "error", "message": str(r)})
      for r in results
    ]

  if path_obj.suffix.lower() != ".pdf":
    raise ValueError("Provided file is not a PDF")
  return [await _process_single_cv(path_obj)]


def _get_llm_transformer() -> LLMGraphTransformer:
  """
  Initializes the LLMGraphTransformer with the specific CV ontology.
  """
  openai_chat_resulta = get_openai_chat(constants.OPENAI_MODEL)
  if openai_chat_resulta.err():
    raise  # TODO: propagate further

  additional_instructions = """
    Ensure skill/technology names use their canonical capitalization:

      Languages: JavaScript, TypeScript, Python, Java, C#, C++, Go, Rust, Ruby, PHP,
    Swift, Kotlin, Scala, HTML, CSS, SCSS, SQL

    Frameworks: React, Vue.js, Angular, Next.js, Nuxt.js, Node.js, Express.js,
    NestJS, FastAPI, Django, Flask, Spring Boot, .NET, Ruby on Rails, Laravel

    Databases: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, Cassandra,
    DynamoDB, SQLite, MariaDB, CockroachDB, Neo4j

    Cloud/DevOps: AWS, Azure, GCP, Docker, Kubernetes, Terraform, Ansible,
    Jenkins, GitLab CI, GitHub Actions, ArgoCD, Helm

    Tools: Git, GitHub, GitLab, Jira, Confluence, Figma, Postman, Swagger,
    OpenAPI, GraphQL, gRPC, RabbitMQ, Kafka, Nginx

    Other: REST, OAuth, JWT, CI/CD, Linux, macOS, iOS, Android, TailwindCSS,
    webpack, Vite, pnpm, npm, yarn
  """

  return LLMGraphTransformer(
    llm=openai_chat_resulta.unwrap(),
    allowed_nodes=constants.ALLOWED_NODES,
    allowed_relationships=constants.ALLOWED_RELATIONSHIPS,
    node_properties=constants.NODE_PROPERTIES,
    strict_mode=True,
    additional_instructions=additional_instructions,
  )
