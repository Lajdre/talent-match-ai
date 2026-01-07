import logging
from typing import Any

from langchain_neo4j import Neo4jGraph

from core.config import config
from src.core.models import RFPStructure

logger = logging.getLogger(__name__)


def get_neo4j_graph() -> Neo4jGraph:
  return Neo4jGraph(
    url=config.NEO4J_URI, username=config.NEO4J_USERNAME, password=config.NEO4J_PASSWORD
  )


def save_rfp_to_graph(rfp_data: RFPStructure):
  """
  Creates the RFP node and connects it to Skill nodes using the NEEDS relationship.
  Uses MERGE to avoid duplicates.
  """
  graph = get_neo4j_graph()

  # Create/Update the RFP Node. Store the core attributes on the node.
  rfp_cypher = """
    MERGE (r:RFP {id: $id})
    SET r.title = $title,
        r.description = $description,
        r.client = $client,
        r.budget = $budget_range,
        r.deadline = $start_date,
        r.location = $location,
        r.team_size = $team_size
    """

  graph.query(rfp_cypher, params=rfp_data.model_dump())

  # Create NEEDS relationships to Skills. Iterate through requirements to link them.
  skill_cypher = """
    MATCH (r:RFP {id: $rfp_id})
    MERGE (s:Skill {id: $skill_name})
    ON CREATE SET s.name = $skill_name

    MERGE (r)-[rel:NEEDS]->(s)
    SET rel.experience_level = $proficiency,
        rel.mandatory = $is_mandatory
    """

  for req in rfp_data.requirements:
    graph.query(
      skill_cypher,
      params={
        "rfp_id": rfp_data.id,
        "skill_name": req.skill_name,
        "proficiency": req.min_proficiency,
        "is_mandatory": req.is_mandatory,
      },
    )

  logger.info(
    f"Saved RFP {rfp_data.id} to Neo4j with {len(rfp_data.requirements)} skill requirements"
  )


def get_graph_metadata() -> dict[str, Any]:
  """
  Retrieves comprehensive statistics, schema details, and validation warnings
  about the current state of the Knowledge Graph.
  """
  graph = get_neo4j_graph()

  try:
    total_nodes = graph.query("MATCH (n) RETURN count(n) as count")[0]["count"]
    total_relationships = graph.query("MATCH ()-[r]->() RETURN count(r) as count")[0][
      "count"
    ]
  except Exception as e:
    logger.error(f"Failed to get basic counts: {e}")
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
  except Exception as e:
    logger.warning(f"Failed to get node breakdown: {e}")

  relationship_type_breakdown = {}
  try:
    query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """
    results = graph.query(query)
    relationship_type_breakdown = {row["type"]: row["count"] for row in results}
  except Exception as e:
    logger.warning(f"Failed to get relationship breakdown: {e}")

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

  if total_nodes > 0 and total_nodes < 10:
    warnings.append("Graph density is very low (under 10 nodes).")

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
  """
  Helper to fetch a few sample nodes of a specific type to verify content.
  """
  graph = get_neo4j_graph()
  try:
    # Sanitize label to prevent injection if exposed directly (simple alphanumeric check)
    if not label.isalnum():
      return []

    query = f"MATCH (n:{label}) RETURN n LIMIT $limit"
    result = graph.query(query, params={"limit": limit})

    # Unwrap the Neo4j Node object to a python dict
    samples = []
    for row in result:
      node = row.get("n")
      if node:
        # properties is usually a dict on the node object
        samples.append(dict(node))
    return samples
  except Exception as e:
    logger.error(f"Failed to get sample for {label}: {e}")
    return []
