from core.models.models import ProjectRead, ProjectStatus, ProjectStructure
from services.neo4j_service import get_neo4j_graph


def upsert_project(project: ProjectStructure):
  """Creates/Updates a Project node and its relationships (Skills, People)."""
  graph = get_neo4j_graph()

  # Merge Project Node
  cypher = """
    MERGE (p:Project {id: $id})
    SET p.title = $name,
        p.description = $description,
        p.client = $client,
        p.start_date = $start_date,
        p.end_date = $end_date,
        p.budget = $budget,
        p.status = $status,
        p.team_size = $team_size
    """
  graph.query(cypher, params=project.model_dump())

  # Merge Skill Requirements
  cypher = """
    MATCH (p:Project {id: $project_id})
    MERGE (s:Skill {id: $skill_name})
    ON CREATE SET s.name = $skill_name

    MERGE (p)-[r:REQUIRES]->(s)
    SET r.minimum_level = $min_proficiency,
        r.mandatory = $is_mandatory
    """

  for req in project.requirements:
    graph.query(
      cypher,
      params={
        "project_id": project.id,
        "skill_name": req.skill_name,
        "min_proficiency": req.min_proficiency,
        "is_mandatory": req.is_mandatory,
      },
    )

  # Merge Assignments (People)
  is_historical = project.status == ProjectStatus.COMPLETED

  rel_type = "WORKED_ON" if is_historical else "ASSIGNED_TO"

  cypher = f"""
    MATCH (p:Project {{id: $project_id}})
    MATCH (u:Person) WHERE u.id = $programmer_name OR u.name = $programmer_name

    MERGE (u)-[r:{rel_type}]->(p)
    SET r.start_date = $start_date,
        r.end_date = $end_date
    """

  for person in project.assigned_programmers:
    graph.query(
      cypher,
      params={
        "project_id": project.id,
        "programmer_name": person.programmer_name,
        "start_date": person.assignment_start_date,
        "end_date": person.assignment_end_date,
      },
    )


def get_projects() -> list[ProjectRead]:
  """
  Fetches projects with requirements and team members.
  """
  cypher = """
    MATCH (p:Project)

    OPTIONAL MATCH (p)-[:REQUIRES]->(s:Skill)

    OPTIONAL MATCH (person:Person)-[r]->(p)
    WHERE type(r) IN ['ASSIGNED_TO', 'WORKED_ON']

    WITH p, collect(distinct s.id) as req_skills,
         collect(distinct {
            name: person.name,
            id: person.id,
            role: r.role
         }) as team

    RETURN {
        id: p.id,
        title: p.title,
        client: p.client,
        status: p.status,
        description: p.description,
        required_skills: req_skills,
        assigned_team: team
    } as data
    ORDER BY p.start_date DESC
    """

  results = get_neo4j_graph().query(cypher)
  return [ProjectRead(**row["data"]) for row in results]
