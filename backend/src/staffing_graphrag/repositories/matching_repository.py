import logging
from typing import Any

from shared_types.matching_types import CandidateMatch, MatchResponse

from services.neo4j_service import get_neo4j_graph

logger = logging.getLogger(__name__)


class MatchingRepository:
  def __init__(self) -> None:
    self.graph = get_neo4j_graph()

  def find_candidates(self, rfp_id: str, max_delay_months: int = 1) -> MatchResponse:
    query = """
      MATCH (r:RFP {id: $rfp_id})
      MATCH (p:Person)

      // COLLECT RFP REQUIREMENTS
      OPTIONAL MATCH (r)-[req:NEEDS]->(s:Skill)
      WITH r, p,
           collect({
             id: s.id,
             mandatory: req.mandatory,
             req_level:
               CASE req.proficiency
                 WHEN 'Beginner' THEN 1
                 WHEN 'Intermediate' THEN 2
                 WHEN 'Advanced' THEN 3
                 WHEN 'Expert' THEN 4
                 ELSE 0
               END
           }) AS requirements

      // COLLECT PERSON SKILLS
      OPTIONAL MATCH (p)-[hs:HAS_SKILL]->(ps:Skill)
      WITH r, p, requirements,
           collect({
             id: ps.id,
             person_level:
               CASE hs.proficiency
                 WHEN 'Beginner' THEN 1
                 WHEN 'Intermediate' THEN 2
                 WHEN 'Advanced' THEN 3
                 WHEN 'Expert' THEN 4
                 ELSE 0
               END
           }) AS person_skills

      // SCORE CALCULATION
      WITH r, p, requirements, person_skills,

      // Total score
      reduce(score = 0, req IN requirements |
        score +
        CASE
          WHEN any(ps IN person_skills WHERE ps.id = req.id) THEN
            CASE
              WHEN req.mandatory THEN
                CASE
                  WHEN (head([ps IN person_skills WHERE ps.id = req.id]).person_level - req.req_level) >= 0 THEN 10
                  WHEN (head([ps IN person_skills WHERE ps.id = req.id]).person_level - req.req_level) = -1 THEN 6
                  ELSE 3
                END
              ELSE
                CASE
                  WHEN (head([ps IN person_skills WHERE ps.id = req.id]).person_level - req.req_level) >= 0 THEN 5
                  WHEN (head([ps IN person_skills WHERE ps.id = req.id]).person_level - req.req_level) = -1 THEN 3
                  ELSE 1
                END
            END
          ELSE 0
        END
      ) AS total_score,

      // Missing skills
      [item IN requirements
       WHERE item.mandatory
         AND NOT any(ps IN person_skills WHERE ps.id = item.id)
       | item.id] AS missing_mandatory,

      [item IN requirements
       WHERE NOT item.mandatory
         AND NOT any(ps IN person_skills WHERE ps.id = item.id)
       | item.id] AS missing_optional,

      // Max possible score
      reduce(max_score = 0, item IN requirements |
        max_score + CASE WHEN item.mandatory THEN 10 ELSE 5 END
      ) AS max_score

      WHERE total_score > 0

      // AVAILABILITY & PROJECT CONTEXT
      OPTIONAL MATCH (p)-[assign:ASSIGNED_TO]->(proj:Project)
      WHERE proj.status IN ['active', 'planned']

      WITH r, p, total_score, max_score,
           missing_mandatory, missing_optional,
           max(date(assign.end_date)) AS last_project_end,
           head(collect(proj.title)) AS last_project_title,
           coalesce(date(r.start_date), date(r.deadline)) AS rfp_start

      WITH r, p, total_score, max_score,
           missing_mandatory, missing_optional,
           last_project_end, last_project_title, rfp_start,
           CASE
             WHEN last_project_end IS NULL THEN -999
             ELSE duration.inDays(rfp_start, last_project_end).days
           END AS delay_days

      RETURN {
        id: p.id,
        name: coalesce(p.name, p.id),
        role: 'Developer',

        total_score: total_score,
        skill_match_percent:
          CASE
            WHEN max_score = 0 THEN 0
            ELSE (toFloat(total_score) / toFloat(max_score)) * 100
          END,

        missing_mandatory: missing_mandatory,
        missing_optional: missing_optional,

        delay_days: delay_days,
        last_end_date: toString(last_project_end),
        last_project_title: last_project_title
      } AS candidate
      ORDER BY total_score DESC
    """

    results = self.graph.query(query, params={"rfp_id": rfp_id})

    response = MatchResponse(rfp_id=rfp_id)

    for row in results:
      data = row["candidate"]
      delay = data["delay_days"]

      if delay <= 0:
        status = "available"
      elif delay <= (max_delay_months * 30):
        status = "available_soon"
      else:
        status = "unavailable"

      candidate = CandidateMatch(
        programmer_id=str(data["id"]),
        programmer_name=data["name"],
        role=data.get("role"),
        total_score=data["total_score"],
        skill_match_percent=round(data["skill_match_percent"], 1),
        missing_mandatory_skills=data["missing_mandatory"],
        missing_optional_skills=data["missing_optional"],
        status=status,
        days_until_available=max(delay, 0),
        current_project_end_date=data["last_end_date"],
        current_project_name=data.get("last_project_title"),
      )

      skill_fit_ok = (
        len(candidate.missing_mandatory_skills) == 0 and candidate.total_score > 0
      )

      if not skill_fit_ok:
        response.partial_matches.append(candidate)
      elif status == "available":
        response.perfect_matches.append(candidate)
      elif status == "available_soon":
        response.future_matches.append(candidate)

    response.perfect_matches.sort(
      key=lambda c: (c.total_score, c.skill_match_percent),
      reverse=True,
    )
    response.future_matches.sort(
      key=lambda c: (c.total_score, c.skill_match_percent),
      reverse=True,
    )
    response.partial_matches.sort(
      key=lambda c: (c.total_score, c.skill_match_percent),
      reverse=True,
    )

    return response

  def convert_rfp_to_project(self, rfp_id: str, programmer_ids: list[str]) -> str:
    """Convert an RFP to a project.

    1. Create Project from RFP
    2. Assign Programmers
    3. Delete RFP
    """
    cypher = """
        MATCH (r:RFP {id: $rfp_id})

        // Create Project Node
        CREATE (p:Project {
            id: 'PROJ-' + r.id,  // Generate a new ID TODO
            title: r.title,
            description: r.description,
            client: r.client,
            budget: r.budget,
            start_date: r.start_date,
            // Calculate end date approximately
            end_date: toString(date(r.start_date) + duration({months: coalesce(r.duration_months, 6)})),
            status: 'active',
            team_size: r.team_size
        })

        // Copy Requirements (RFP)-[:NEEDS]->(Skill) ==> (Project)-[:REQUIRES]->(Skill)
        WITH r, p
        MATCH (r)-[needs:NEEDS]->(s:Skill)
        CREATE (p)-[req:REQUIRES]->(s)
        SET req.minimum_level = needs.proficiency,
            req.mandatory = needs.mandatory

        // Assign Selected Programmers
        WITH r, p
        MATCH (u:Person)
        WHERE u.id IN $programmer_ids OR toInteger(u.id) IN $programmer_ids

        CREATE (u)-[assign:ASSIGNED_TO]->(p)
        SET assign.start_date = p.start_date,
            assign.end_date = p.end_date,
            assign.allocation_percentage = 100

        // Delete the RFP
        DETACH DELETE r

        RETURN p.id as new_project_id
        """

    result: list[dict[str, Any]] = self.graph.query(
      cypher, params={"rfp_id": rfp_id, "programmer_ids": programmer_ids}
    )

    if not result:
      raise ValueError(f"Failed to convert RFP {rfp_id}. It might not exist.")

    return result[0]["new_project_id"]
