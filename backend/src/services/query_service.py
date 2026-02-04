import logging
from typing import Any

from langchain_neo4j import GraphCypherQAChain

from core import prompts
from core.config import config
from services.neo4j_service import get_neo4j_graph
from services.openai_service import get_openai_chat

logger = logging.getLogger(__name__)


def _get_qa_chain() -> GraphCypherQAChain:
  graph = get_neo4j_graph()

  openai_chat_resulta = get_openai_chat(config.OPENAI_GRAPH_QUERY_MODEL)
  if openai_chat_resulta.err():
    assert False  # TODO: propagate further # noqa: B011, PT015

  return GraphCypherQAChain.from_llm(
    llm=openai_chat_resulta.ok(),
    graph=graph,
    verbose=True,
    cypher_prompt=prompts.cypher_generation_prompt,
    qa_prompt=prompts.cypher_qa_prompt,
    return_intermediate_steps=True,
    allow_dangerous_requests=True,
    validate_cypher=True,
  )


async def process_query(question: str) -> dict[str, Any]:
  """Execute a natural language query against the Knowledge Graph."""
  try:
    chain = _get_qa_chain()

    result: dict[str, Any] = await chain.ainvoke({"query": question})

    # Extract intermediate step (the actual Cypher query generated)
    cypher_query = ""
    steps = result.get("intermediate_steps", [])
    if steps and isinstance(steps[0], dict):
      cypher_query = steps[0].get("query", "")

    return {
      "question": question,
      "answer": result.get("result", "No answer generated"),
      "cypher_query": cypher_query,
      "success": True,
    }

  except Exception as e:
    logger.exception("Graph QA failed.")
    return {
      "question": question,
      "answer": "I encountered an error processing your query.",
      "error": str(e),
      "success": False,
    }


def get_example_queries_list() -> dict[str, list[str]]:
  """Return a categorized list of example queries for the frontend."""
  return {
    "Basic Information": [
      "How many people are in the knowledge graph?",
      "Who has both Docker and Kubernetes skills?",
      "Find people who worked at the same companies.",
      "Find people who are currently assigned to the same project.",
    ],
    "Skill-based Queries": [
      "Who has cloud computing skills like AWS?",
      "What programming languages are most common?",
    ],
    "Company Experience": [
      "What companies have the most former employees in our database?",
      "List all companies mentioned in the CVs.",
    ],
    "Education Background": [
      "Find people who studied at Ivy League schools.",
      "What universities are most common in our database?",
      "Find people that studied at the same university.",
    ],
    "Location and Geography": [
      "What cities have the most people?",
      "Who is located in Deniseborough?",
      "Show all locations in our database.",
    ],
    "Certification Analysis": [
      "Who has AWS certifications?",
      "Find all Google Cloud certified people.",
      "What are the most common certifications?",
    ],
  }
