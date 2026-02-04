from shared_types.programmer_types import ProgrammerRead

from services.neo4j_service import get_neo4j_graph


def get_programmers(status: str | None = None) -> list[ProgrammerRead]:
  cypher = """
    MATCH (p:Person)

    OPTIONAL MATCH (p)-[hs:HAS_SKILL]->(s:Skill)
    WITH p, collect({
      skill: s.id,
      proficiency: hs.proficiency
    }) AS raw_skills

    OPTIONAL MATCH (p)-[:ASSIGNED_TO]->(proj:Project)
    WHERE proj.status IN ['active', 'planned']
    WITH
      p,
      raw_skills,
      collect(DISTINCT proj.title) AS active_projects

    RETURN {
      id: p.id,
      name: p.name,
      location: p.location,
      skills: {
        Expert: [x IN raw_skills WHERE x.proficiency = 'Expert' | x.skill],
        Advanced: [x IN raw_skills WHERE x.proficiency = 'Advanced' | x.skill],
        Intermediate: [x IN raw_skills WHERE x.proficiency = 'Intermediate' | x.skill],
        Beginner: [x IN raw_skills WHERE x.proficiency = 'Beginner' | x.skill]
      },
      is_assigned: size(active_projects) > 0,
      current_project: head(active_projects)
    } AS data
  """

  results = get_neo4j_graph().query(cypher)
  parsed_results = [ProgrammerRead(**row["data"]) for row in results]

  if status == "available":
    return [p for p in parsed_results if not p.is_assigned]
  if status == "assigned":
    return [p for p in parsed_results if p.is_assigned]

  return parsed_results
