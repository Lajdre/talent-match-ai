from typing import Literal

from pydantic import BaseModel, EmailStr, Field

ProficiencyLevel = Literal["Beginner", "Intermediate", "Advanced", "Expert"]


class CVSkill(BaseModel):
  skill_name: str
  proficiency: ProficiencyLevel = Field(
    description="Must be one of: Beginner, Intermediate, Advanced, Expert"
  )


class CVStructure(BaseModel):
  full_name: str
  email: EmailStr | None = None
  location: str | None = None
  summary: str | None = None
  university_name: str | None = None
  certifications: list[str] = Field(default_factory=list)
  worked_for: list[str] = Field(default_factory=list)
  skills: list[CVSkill] = Field(default_factory=list)
