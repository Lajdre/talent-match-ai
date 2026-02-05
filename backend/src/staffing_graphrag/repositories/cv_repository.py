from core.models.cv_models import CVStructure
from services.neo4j_service import get_neo4j_graph


def upsert_cv(cv: CVStructure) -> None:
  graph = get_neo4j_graph()

  def merge_person() -> None:
    cypher = """
      MERGE (p:Person {id: $full_name})
      SET p.name = $full_name,
          p.email = $email,
          p.bio = $summary
    """
    graph.query(
      cypher,
      params={
        "full_name": cv.full_name,
        "email": cv.email,
        "summary": cv.summary,
      },
    )

  def merge_skills() -> None:
    cypher = """
      MATCH (p:Person {id: $person_name})
      MERGE (s:Skill {id: $skill_name})
      ON CREATE SET s.name = $skill_name

      MERGE (p)-[r:HAS_SKILL]->(s)
      SET r.proficiency = $proficiency
    """
    for skill in cv.skills:
      graph.query(
        cypher,
        params={
          "person_name": cv.full_name,
          "skill_name": skill.skill_name.strip().title(),
          "proficiency": skill.proficiency.strip().title(),
        },
      )

  def merge_work_history() -> None:
    cypher = """
      MATCH (p:Person {id: $person_name})
      MERGE (c:Company {id: $company_name})
      ON CREATE SET c.name = $company_name

      MERGE (p)-[:WORKED_AT]->(c)
    """
    for company_name in cv.worked_for:
      graph.query(
        cypher,
        params={
          "person_name": cv.full_name,
          "company_name": company_name.strip().title(),
        },
      )

  def merge_education() -> None:
    if not cv.university_name:
      return

    cypher = """
      MATCH (p:Person {id: $person_name})
      MERGE (u:University {id: $uni_name})
      ON CREATE SET u.name = $uni_name

      MERGE (p)-[:STUDIED_AT]->(u)
    """
    graph.query(
      cypher,
      params={
        "person_name": cv.full_name,
        "uni_name": cv.university_name.strip().title(),
      },
    )

  def merge_certifications() -> None:
    cypher = """
      MATCH (p:Person {id: $person_name})
      MERGE (c:Certification {id: $cert_name})
      ON CREATE SET c.name = $cert_name

      MERGE (p)-[:EARNED]->(c)
    """
    for cert_name in cv.certifications:
      graph.query(
        cypher,
        params={
          "person_name": cv.full_name,
          "cert_name": cert_name.strip().title(),
        },
      )

  def merge_location() -> None:
    if not cv.location:
      return

    cypher = """
      MATCH (p:Person {id: $person_name})
      MERGE (l:Location {id: $location_name})
      ON CREATE SET l.name = $location_name

      MERGE (p)-[:LOCATED_IN]->(l)
    """
    graph.query(
      cypher,
      params={
        "person_name": cv.full_name,
        "location_name": cv.location.strip().title(),
      },
    )

  merge_person()
  merge_skills()
  merge_work_history()
  merge_education()
  merge_certifications()
  merge_location()
