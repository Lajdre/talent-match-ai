from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

### Matching Algorithm models


class CandidateMatch(BaseModel):
  programmer_id: str
  programmer_name: str
  role: str | None = None
  total_score: float
  skill_match_percent: float
  missing_mandatory_skills: list[str] = []
  status: Literal["available", "available_soon", "unavailable"]
  days_until_available: int
  current_project_end_date: str | None = None


class MatchResponse(BaseModel):
  rfp_id: str
  perfect_matches: list[CandidateMatch] = []  # Available & Skilled
  future_matches: list[CandidateMatch] = []  # Skilled but busy briefly
  partial_matches: list[CandidateMatch] = []  # Available but missing mandatory skills


class AssignmentRequest(BaseModel):
  programmer_ids: list[str]  # List of IDs to assign


### Read Models for UI. Should move to schemas


class ProgrammerRead(BaseModel):
  id: str
  name: str | None = None
  role: str | None = None
  location: str | None = None
  skills: list[str] = []
  is_assigned: bool = False
  current_project: str | None = None


class ProjectRead(BaseModel):
  id: str
  title: str | None = None
  client: str | None = None
  status: str | None = None
  description: str | None = None
  required_skills: list[str] = []
  assigned_team: list[dict[str, Any]] = []  # Simple list of names/roles


class RFPRead(BaseModel):
  id: str
  title: str | None = None
  client: str | None = None
  budget: str | None = None
  needed_skills: list[dict[str, Any]] = []  # Skill + proficiency level


### Projects types


class ProjectStatus(str, Enum):
  COMPLETED = "completed"
  ACTIVE = "active"
  PLANNED = "planned"
  ON_HOLD = "on_hold"


class AssignedProgrammer(BaseModel):
  programmer_name: str
  programmer_id: int  # Keeping ID from JSON, though we match on Name usually
  assignment_start_date: str | None = None
  assignment_end_date: str | None = None


class ProjectRequirement(BaseModel):
  skill_name: str
  min_proficiency: str
  is_mandatory: bool


class ProjectStructure(BaseModel):
  id: str
  name: str
  client: str
  description: str
  start_date: str | None = None
  end_date: str | None = None
  estimated_duration_months: int | None = None
  budget: int | None = None
  status: ProjectStatus
  team_size: int
  requirements: list[ProjectRequirement] = []
  assigned_programmers: list[AssignedProgrammer] = []
