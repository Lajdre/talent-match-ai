from enum import Enum

from pydantic import BaseModel


class ProjectStatus(str, Enum):
  COMPLETED = "completed"
  ACTIVE = "active"
  PLANNED = "planned"
  ON_HOLD = "on_hold"


class _AssignedProgrammer(BaseModel):
  programmer_name: str
  programmer_id: int
  assignment_start_date: str | None = None
  assignment_end_date: str | None = None


class _ProjectRequirement(BaseModel):
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
  requirements: list[_ProjectRequirement] = []
  assigned_programmers: list[_AssignedProgrammer] = []
