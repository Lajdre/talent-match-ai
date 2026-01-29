from pydantic import BaseModel, Field


class ProgrammerRead(BaseModel):
  id: str
  name: str | None = None
  role: str | None = None
  location: str | None = None
  is_assigned: bool = False
  current_project: str | None = None
  skills: dict[str, list[str]] = Field(
    default_factory=lambda: {
      "Expert": [],
      "Advanced": [],
      "Intermediate": [],
      "Beginner": [],
    }
  )
