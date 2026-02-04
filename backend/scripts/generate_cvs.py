import json
import os
import random
import textwrap
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from faker import Faker
from openai import OpenAI

from scripts.common import save_markdown_as_pdf


def generate_skills() -> list[dict]:
  all_skills = [
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C++",
    "Go",
    "Rust",
    "React",
    "Vue.js",
    "Angular",
    "Node.js",
    "Django",
    "Flask",
    "FastAPI",
    "PostgreSQL",
    "MongoDB",
    "Redis",
    "MySQL",
    "AWS",
    "Docker",
    "Kubernetes",
    "Jenkins",
    "Git",
    "Machine Learning",
    "Data Science",
    "DevOps",
    "Microservices",
  ]
  proficiency_levels = ["Beginner", "Intermediate", "Advanced", "Expert"]
  num_skills = random.randint(5, 12)
  selected = random.sample(all_skills, num_skills)
  weights = [5, 30, 40, 25]
  return [
    {
      "name": skill,
      "proficiency": random.choices(proficiency_levels, weights=weights)[0],
    }
    for skill in selected
  ]


def generate_projects() -> list[str]:
  pool = [
    "E-commerce Platform",
    "Data Analytics Dashboard",
    "Mobile App",
    "API Gateway",
    "Machine Learning Pipeline",
    "Web Application",
    "Microservices Architecture",
    "Real-time Chat System",
    "Content Management System",
    "Payment Processing System",
  ]
  return random.sample(pool, random.randint(2, 5))


def generate_certifications() -> list[str]:
  pool = [
    "AWS Certified Solutions Architect",
    "Google Cloud Professional",
    "Certified Kubernetes Administrator",
    "Microsoft Azure Developer",
    "Scrum Master Certification",
    "Docker Certified Associate",
  ]
  return random.sample(pool, random.randint(0, 3)) if random.randint(0, 3) else []


def generate_cv_markdown(profile: dict, openai_client: OpenAI) -> str:
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    raise ValueError("OPENAI_API_KEY not set")

  skills_text = [f"{s['name']} ({s['proficiency']})" for s in profile["skills"]]
  prompt = textwrap.dedent(f"""
        Create a professional CV in markdown format for a programmer with:
        Name: {profile["name"]}
        Email: {profile["email"]}
        Location: {profile["location"]}
        Skills: {", ".join(skills_text)}
        Projects: {", ".join(profile["projects"])}
        Certifications: {", ".join(profile["certifications"])}

        Requirements:
        - Use markdown (#, -, **, etc.)
        - Vary structure/tone; make it personal and realistic
        - Include specific metrics, company names, dates
        - Integrate proficiency levels naturally
        - Return ONLY markdown content (no ```markdown blocks)
    """)

  response = openai_client.responses.create(
    model="gpt-4o-mini", input=prompt, temperature=0.7
  )
  content = response.output_text

  if not content:
    raise ValueError(f"Empty CV for {profile['name']}")

  return content.replace("```markdown", "").replace("```", "").strip()


def generate_project_records(
  programmer_profiles: list[dict], num_projects: int, faker: Faker
) -> list[dict]:
  project_types = [
    "E-commerce Platform",
    "Data Analytics Dashboard",
    "Mobile App Development",
    "API Gateway Implementation",
    "Machine Learning Pipeline",
    "Web Application",
    "Microservices Architecture",
    "Real-time Chat System",
    "Content Management System",
    "Payment Processing System",
    "DevOps Automation",
    "Cloud Migration",
    "Security Audit System",
    "Inventory Management",
    "Customer Portal",
  ]
  clients = [
    "TechCorp",
    "DataSystems Inc",
    "CloudNative Solutions",
    "FinTech Innovations",
    "HealthTech Partners",
    "RetailMax",
    "LogisticsPro",
    "EduTech Solutions",
    "MediaStream",
    "GreenEnergy Co",
    "SmartCity Initiative",
    "BioTech Labs",
  ]

  # collect unique skills from profiles
  available_skills = set()
  for profile in programmer_profiles:
    for skill in profile["skills"]:
      available_skills.add(skill["name"])
  skill_names = list(available_skills)

  projects = []
  for i in range(num_projects):
    start_date = faker.date_between(start_date="-2y", end_date="+6m")
    duration_months = random.randint(3, 18)

    status = random.choices(
      ["completed", "active", "planned", "on_hold"],
      weights=[50, 30, 15, 5],
    )[0]

    end_date = (
      (start_date + timedelta(days=duration_months * 30)).isoformat()
      if status == "completed"
      else None
    )

    num_requirements = random.randint(2, 5)
    required_skills = random.sample(skill_names, num_requirements)
    requirements = [
      {
        "skill_name": skill,
        "min_proficiency": random.choice(
          ["Beginner", "Intermediate", "Advanced", "Expert"]
        ),
        "is_mandatory": random.choice([True, True, False]),
      }
      for skill in required_skills
    ]

    project = {
      "id": f"PRJ-{i + 1:03d}",
      "title": f"{random.choice(project_types)} for {random.choice(clients)}",
      "client": random.choice(clients),
      "description": f"Development of {random.choice(project_types).lower()} with focus on scalability and performance",
      "start_date": start_date.isoformat(),
      "end_date": end_date,
      "estimated_duration_months": duration_months,
      "budget": random.randint(50000, 500000) if random.choice([True, False]) else None,
      "status": status,
      "team_size": random.randint(3, 5),
      "requirements": requirements,
      "assigned_programmers": [],
    }
    projects.append(project)

  return assign_programmers_to_projects(projects, programmer_profiles)


def assign_programmers_to_projects(  # noqa: PLR0915
  projects: list[dict], programmer_profiles: list[dict]
) -> list[dict]:
  """Assign programmers to projects based on skill matching, leaving some unassigned."""
  # Create a list to track programmer availability periods
  programmer_assignments = {p["id"]: [] for p in programmer_profiles}

  def has_skill_requirement(
    programmer: dict, skill_name: str, min_proficiency: str
  ) -> bool:
    proficiency_levels = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Expert": 4}
    min_level = proficiency_levels[min_proficiency]

    for skill in programmer["skills"]:
      if skill["name"] == skill_name:
        programmer_level = proficiency_levels[skill["proficiency"]]
        return programmer_level >= min_level
    return False

  def is_available(programmer_id: dict, start_date: str, end_date: str) -> bool:
    assignments = programmer_assignments[programmer_id]
    project_start = datetime.fromisoformat(start_date).date()
    project_end = datetime.fromisoformat(end_date).date() if end_date else None

    for assignment in assignments:
      assign_start = datetime.fromisoformat(assignment["assignment_start_date"]).date()
      assign_end = (
        datetime.fromisoformat(assignment["assignment_end_date"]).date()
        if assignment["assignment_end_date"]
        else None
      )

      # Check for overlap
      if assign_end is None:  # Ongoing assignment
        if project_end is None or project_start <= assign_start:
          return False
      elif project_end is None:  # Ongoing project
        if assign_end >= project_start:
          return False
      elif not (project_end < assign_start or project_start > assign_end):
        return False
    return True

  # Process only active and completed projects for assignments
  assignable_projects = [p for p in projects if p["status"] in ["active", "completed"]]

  # Assign programmers to projects (configurable percentage to leave some available)
  assignment_probability = 0.7

  for project in assignable_projects:
    if random.random() > assignment_probability:
      continue  # Skip this project to leave programmers available

    assigned_count = 0
    max_assignments = min(project["team_size"], len(programmer_profiles))

    # Get mandatory requirements
    mandatory_requirements = [
      req for req in project["requirements"] if req["is_mandatory"]
    ]

    # Try to find programmers matching mandatory skills
    eligible_programmers = []
    for programmer in programmer_profiles:
      matches_mandatory = True
      for req in mandatory_requirements:
        if not has_skill_requirement(
          programmer, req["skill_name"], req["min_proficiency"]
        ):
          matches_mandatory = False
          break

      if matches_mandatory and is_available(
        programmer["id"], project["start_date"], project["end_date"]
      ):
        eligible_programmers.append(programmer)

    # Randomly select from eligible programmers
    selected_programmers = random.sample(
      eligible_programmers, min(max_assignments, len(eligible_programmers))
    )

    # Create assignments
    for programmer in selected_programmers:
      # Calculate assignment dates based on project dates
      assignment_start = project["start_date"]

      # Always calculate assignment end date (before project end)
      if project["status"] == "completed":
        # For completed projects, assignment ends before or at project end
        project_end = datetime.fromisoformat(project["end_date"]).date()
        project_start = datetime.fromisoformat(project["start_date"]).date()
        project_duration = (project_end - project_start).days

        # Assignment ends configurable days before project end (but at least 1 day after start)
        days_before_end = min(
          random.randint(1, 30),
          max(1, project_duration - 1),
        )
        assignment_end_date = project_end - timedelta(days=days_before_end)
        assignment_end = assignment_end_date.isoformat()

      elif project["status"] == "active":
        # For active projects, calculate end date based on estimated duration
        project_start = datetime.fromisoformat(project["start_date"]).date()
        estimated_end = project_start + timedelta(
          days=project["estimated_duration_months"] * 30
        )

        # Assignment ends configurable days before estimated project end
        days_before_end = random.randint(1, 30)
        assignment_end_date = estimated_end - timedelta(days=days_before_end)
        assignment_end = assignment_end_date.isoformat()

      # For other statuses, use project end date if available
      elif project["end_date"]:
        project_end = datetime.fromisoformat(project["end_date"]).date()
        project_start = datetime.fromisoformat(project["start_date"]).date()
        project_duration = (project_end - project_start).days
        days_before_end = random.randint(1, 30)
        days_before_end = min(
          random.randint(1, 30),
          max(1, project_duration - 1),
        )
        assignment_end_date = project_end - timedelta(days=days_before_end)
        assignment_end = assignment_end_date.isoformat()
      else:
        # Fallback: use estimated duration
        project_start = datetime.fromisoformat(project["start_date"]).date()
        estimated_end = project_start + timedelta(
          days=project["estimated_duration_months"] * 30
        )
        days_before_end = random.randint(1, 30)
        assignment_end_date = estimated_end - timedelta(days=days_before_end)
        assignment_end = assignment_end_date.isoformat()

      assignment = {
        "programmer_name": programmer["name"],
        "programmer_id": programmer["id"],
        "assignment_start_date": assignment_start,
        "assignment_end_date": assignment_end,
      }

      project["assigned_programmers"].append(assignment)
      programmer_assignments[programmer["id"]].append(assignment)
      assigned_count += 1

  return projects


def generate_single_cv(
  profile_id: int, output_dir: Path, faker: Faker, openai_client: OpenAI
) -> tuple[Path, dict]:
  profile = {
    "id": profile_id,
    "name": faker.name(),
    "email": faker.email(),
    "location": faker.city(),
    "skills": generate_skills(),
    "projects": generate_projects(),
    "certifications": generate_certifications(),
  }
  md: str = generate_cv_markdown(profile, openai_client)
  safe_name: str = profile["name"].replace(" ", "_").replace(".", "")
  pdf_path = save_markdown_as_pdf(md, f"cv_{profile_id:03d}_{safe_name}", output_dir)
  return pdf_path, profile


def generate_cvs(
  num: int, output_dir: Path, faker: Faker, openai_client: OpenAI
) -> tuple[list[Path], list[dict]]:
  paths: list[Path] = []
  profiles: list[dict] = []

  for i in range(num):
    path, profile = generate_single_cv(i + 1, output_dir, faker, openai_client)
    paths.append(path)
    profiles.append(profile)

  return paths, profiles


if __name__ == "__main__":
  NUM_PROGRAMMERS = 4
  NUM_PROJECTS = 2
  OUTPUT_DIR = Path("data/programmers")
  PROJECTS_FILE = Path("data/projects.json")

  load_dotenv(override=True)
  openai_client = OpenAI()
  faker = Faker()

  print("Generating CVs ...")

  try:
    cv_paths, profiles = generate_cvs(NUM_PROGRAMMERS, OUTPUT_DIR, faker, openai_client)
    print(f"Generated {len(cv_paths)} CVs in {OUTPUT_DIR}/")

    projects = generate_project_records(profiles, NUM_PROJECTS, faker)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with PROJECTS_FILE.open("w", encoding="utf-8") as f:
      json.dump(projects, f, indent=2, default=str)
    print(f"Saved {len(projects)} projects to {PROJECTS_FILE}")
  except Exception as e:
    print("Error:", e)
    raise
