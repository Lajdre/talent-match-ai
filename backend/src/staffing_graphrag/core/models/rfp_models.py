from pydantic import BaseModel, Field


class SkillRequirement(BaseModel):
  skill_name: str = Field(
    description="The name of the technical skill (e.g., Python, AWS)"
  )
  min_proficiency: str = Field(
    description="Must be one of: Beginner, Intermediate, Advanced, Expert"
  )
  is_mandatory: bool = Field(
    description="True if listed as Required/Mandatory, False if Preferred/Nice-to-have"
  )
  preferred_certifications: list[str] = Field(
    default_factory=list, description="List of certifications mentioned for this skill"
  )


class RFPStructure(BaseModel):
  id: str | None = Field(default=None, description="The RFP ID (assigned by system)")
  title: str = Field(description="Project title")
  client: str = Field(description="Name of the client company")
  description: str = Field(description="Short summary of the project")
  project_type: str = Field(
    description="Category of the project (e.g., DevOps, Web App)"
  )
  duration_months: int = Field(description="Project duration in months")
  team_size: int = Field(description="Required team size")
  budget_range: str = Field(description="The budget range specified")
  start_date: str = Field(description="Project start date (YYYY-MM-DD)")
  location: str = Field(description="Project location")
  remote_allowed: bool = Field(description="Is remote work explicitly allowed?")
  requirements: list[SkillRequirement] = Field(
    description="List of technical skill requirements"
  )
