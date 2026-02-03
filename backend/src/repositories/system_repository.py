import logging
from typing import Any

from services.neo4j_service import get_neo4j_graph

logger = logging.getLogger(__name__)


def get_graph_metadata() -> dict[str, Any]:
  """Retrieve graph metadata.

  Returns comprehensive statistics, schema details, and validation warnings
  about the current state of the Knowledge Graph.
  """
  graph = get_neo4j_graph()

  try:
    total_nodes = graph.query("MATCH (n) RETURN count(n) as count")[0]["count"]
    total_relationships = graph.query("MATCH ()-[r]->() RETURN count(r) as count")[0][
      "count"
    ]
  except Exception:
    logger.exception("Failed to get basic counts.")
    return {"error": "Could not connect to database"}

  node_breakdown = {}
  try:
    query = """
      MATCH (n)
      UNWIND labels(n) as label
      WITH label, count(n) as count
      WHERE label <> '__Entity__'
      RETURN label, count ORDER BY label
    """
    results = graph.query(query)
    node_breakdown = {row["label"]: row["count"] for row in results}
  except Exception:
    logger.exception("Failed to get node breakdown.")

  relationship_type_breakdown = {}
  try:
    query = """
      MATCH ()-[r]->()
      RETURN type(r) as type, count(r) as count
      ORDER BY count DESC
    """
    results = graph.query(query)
    relationship_type_breakdown = {row["type"]: row["count"] for row in results}
  except Exception:
    logger.exception("Failed to get relationship breakdown.")

  # Checks if the specific connections we care about actually exist
  key_patterns = {
    "Person -> Skill": "MATCH (p:Person)-[:HAS_SKILL]->(s:Skill) RETURN count(*) as count",
    "Person -> Company": "MATCH (p:Person)-[:WORKED_AT]->(c:Company) RETURN count(*) as count",
    "Person -> Project": "MATCH (p:Person)-[:WORKED_ON]->(pr:Project) RETURN count(*) as count",
  }

  domain_stats = {}
  for name, query in key_patterns.items():
    try:
      res = graph.query(query)
      count = res[0]["count"] if res else 0
      if count > 0:
        domain_stats[name] = count
    except Exception:
      pass

  warnings = []
  if total_nodes == 0:
    warnings.append("Graph is empty.")
  elif node_breakdown.get("Person", 0) == 0:
    warnings.append("No 'Person' nodes found. CV ingestion might have failed.")

  return {
    "status": "healthy" if not warnings else "warning",
    "warnings": warnings,
    "summary": {
      "total_nodes": total_nodes,
      "total_relationships": total_relationships,
    },
    "schema": {
      "nodes": node_breakdown,
      "relationships": relationship_type_breakdown,
    },
    "domain_stats": domain_stats,
  }


def get_node_sample(label: str, limit: int = 5) -> list[dict[str, Any]]:
  """Fetch a few sample nodes of a specific type to verify content."""
  graph = get_neo4j_graph()
  try:
    # Sanitize label
    if not label.isalnum():
      return []

    query = f"MATCH (n:{label}) RETURN n LIMIT $limit"
    result = graph.query(query, params={"limit": limit})

    # Unwrap the Neo4j Node object to a python dict
    samples = []
    for row in result:
      node = row.get("n")
      if node:
        samples.append(dict(node))
    return samples
  except Exception:
    logger.exception("Failed to get sample for %s.", label)
    return []
