from pathlib import Path

RFP_STORAGE_DIR = Path("data/RFP")
RFP_JSON_FILE = RFP_STORAGE_DIR / "rfps.json"

ALLOWED_NODES = [
  "Person",
  "Company",
  "University",
  "Skill",
  "Project",
  "Certification",
  "Location",
  "RFP",
]

ALLOWED_RELATIONSHIPS = [
  ("Person", "WORKED_AT", "Company"),
  ("Person", "STUDIED_AT", "University"),
  ("Person", "HAS_SKILL", "Skill"),
  ("Person", "LOCATED_IN", "Location"),
  ("Person", "WORKED_ON", "Project"),
  ("Person", "EARNED", "Certification"),
  ("Project", "REQUIRES", "Skill"),
  ("Person", "ASSIGNED_TO", "Project"),
  ("RFP", "NEEDS", "Skill"),
  ("RFP", "LOCATED_IN", "Location"),
]

NODE_PROPERTIES = ["start_date", "end_date", "proficiency"]
