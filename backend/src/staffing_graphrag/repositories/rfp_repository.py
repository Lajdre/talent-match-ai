import logging

from shared_types.rfp_types import RFPRead

from core.models.rfp_models import RFPStructure
from services.neo4j_service import get_neo4j_graph

logger = logging.getLogger(__name__)


def get_rfps() -> list[RFPRead]:
  """Fetch RFPs with needed skills."""
  cypher = """
    MATCH (r:RFP)

    OPTIONAL MATCH (r)-[rel:NEEDS]->(s:Skill)

    WITH r, collect({
      name: s.id,
      level: rel.proficiency, // TODO: change level to proficiency
      mandatory: rel.mandatory
      }) as skills

    RETURN {
      id: r.id,
      title: r.title,
      client: r.client,
      budget: r.budget,
      needed_skills: skills
      } as data
    ORDER BY r.id
  """

  results = get_neo4j_graph().query(cypher)
  return [RFPRead(**row["data"]) for row in results]


def get_next_rfp_id() -> str:
  """Get the next available RFP ID from Neo4j."""
  graph = get_neo4j_graph()
  result = graph.query("""
        MATCH (r:RFP)
        RETURN r.id AS id
        ORDER BY r.id DESC
        LIMIT 1
    """)
  if not result:
    return "RFP-001"

  last_id = result[0]["id"]  # e.g., "RFP-042"
  num = int(last_id.split("-")[1]) + 1
  return f"RFP-{num:03d}"


def save_rfp(rfp_data: RFPStructure) -> None:
  """Create the RFP node and connects it to Skill nodes using the NEEDS relationship.

  Fails if the RFP node already exists.
  """
  graph = get_neo4j_graph()

  exists_cypher = """
    MATCH (r:RFP {id: $id})
    RETURN r.id AS id
    LIMIT 1
  """
  if graph.query(exists_cypher, params={"id": rfp_data.id}):
    raise ValueError(f"RFP with id '{rfp_data.id}' already exists.")
    # TODO: provide a nice message

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

  # Create NEEDS relationships to Skills
  skill_cypher = """
    MATCH (r:RFP {id: $rfp_id})
    MERGE (s:Skill {id: $skill_name})
    ON CREATE SET s.name = $skill_name

    MERGE (r)-[rel:NEEDS]->(s)
    SET rel.proficiency = $proficiency,
        rel.mandatory = $is_mandatory
    """

  for req in rfp_data.requirements:
    graph.query(
      skill_cypher,
      params={
        "rfp_id": rfp_data.id,
        "skill_name": req.skill_name.strip().title(),
        "proficiency": req.min_proficiency.strip().title(),
        "is_mandatory": req.is_mandatory,
      },
    )

  logger.info(
    "Saved RFP %s to Neo4j with %s skill requirements",
    rfp_data.id,
    len(rfp_data.requirements),
  )
