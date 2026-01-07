import logging

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
