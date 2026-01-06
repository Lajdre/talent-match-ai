import os
import random
import textwrap
from pathlib import Path

from dotenv import load_dotenv
from faker import Faker
from openai import OpenAI

from .utils import save_markdown_as_pdf


def generate_rfps_data_dicts(num_rfps: int, fake: Faker) -> list[dict]:
  """Generate Request for Proposal docs."""
  if num_rfps <= 0:
    raise ValueError("Number of RFPs must be positive")

  rfp_types = [
    "Enterprise Web Application",
    "Mobile App Development",
    "Data Analytics Platform",
    "Cloud Migration Project",
    "E-commerce Modernization",
    "API Integration Platform",
    "Machine Learning Implementation",
    "DevOps Automation",
    "Security Enhancement",
  ]

  clients = [
    "Global Finance Corp",
    "MedTech Industries",
    "Retail Solutions Ltd",
    "Manufacturing Plus",
    "Education Network",
    "Energy Systems Co",
  ]

  budget_ranges = ["$100K - $250K", "$250K - $500K", "$500K - $1M", "$1M - $2M"]

  skill_names = [
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "React",
    "Angular",
    "Node.js",
    "Django",
    "AWS",
    "Docker",
    "Kubernetes",
    "PostgreSQL",
    "MongoDB",
    "Machine Learning",
    "DevOps",
    "Microservices",
  ]

  rfps = []
  for i in range(num_rfps):
    start_date = fake.date_between(start_date="+1m", end_date="+6m")

    num_requirements = random.randint(4, 10)
    requirements = []
    required_skills = random.sample(skill_names, num_requirements)

    for skill in required_skills:
      requirements.append(
        {
          "skill_name": skill,
          "min_proficiency": random.choice(["Intermediate", "Advanced", "Expert"]),
          "is_mandatory": random.choice([True, True, False]),
          "preferred_certifications": random.sample(
            [
              "AWS Certified Solutions Architect",
              "Google Cloud Professional",
              "Certified Kubernetes Administrator",
            ],
            random.randint(0, 2),
          ),
        }
      )

    rfp = {
      "id": f"RFP-{i + 1:03d}",
      "title": f"{random.choice(rfp_types)} Development",
      "client": random.choice(clients),
      "description": f"Seeking experienced development team for {random.choice(rfp_types).lower()}",
      "project_type": random.choice(rfp_types),
      "duration_months": random.randint(6, 24),
      "team_size": random.randint(3, 12),
      "budget_range": random.choice(budget_ranges),
      "start_date": start_date.isoformat(),
      "requirements": requirements,
      "location": fake.city(),
      "remote_allowed": random.choice([True, True, False]),
    }
    rfps.append(rfp)

  return rfps


def generate_rfp_markdown(
  rfp: dict, openai_clinet: OpenAI, generator_model: str
) -> str:
  requirements_text = []
  for req in rfp["requirements"]:
    cert_text = (
      f" (Preferred certifications: {', '.join(req['preferred_certifications'])})"
      if req["preferred_certifications"]
      else ""
    )
    mandatory_text = "REQUIRED" if req["is_mandatory"] else "Preferred"
    requirements_text.append(
      f"- {mandatory_text}: {req['skill_name']} - {req['min_proficiency']} level{cert_text}"
    )

  prompt = textwrap.dedent(f"""
    Create a professional RFP (Request for Proposal) document in markdown format with the following details:

    Project: {rfp["title"]}
    Client: {rfp["client"]}
    Project Type: {rfp["project_type"]}
    Description: {rfp["description"]}
    Duration: {rfp["duration_months"]} months
    Team Size: {rfp["team_size"]} people
    Budget Range: {rfp["budget_range"]}
    Start Date: {rfp["start_date"]}
    Location: {rfp["location"]}
    Remote Work: {"Allowed" if rfp["remote_allowed"] else "Not allowed"}

    Technical Requirements:
    {chr(10).join(requirements_text)}

    Requirements:
    1. Use proper markdown formatting (headers, lists, emphasis)
    2. Structure as a professional PRD (Product Requirements Document)
    3. Include sections like: Executive Summary, Project Overview, Technical Requirements, Expected Team Profile, Timeline, Budget, Proposal Guidelines
    4. Create realistic business context and objectives
    5. Add specific deliverables and milestones
    6. Include detailed descriptions of the expected programmer profiles
    7. Make it sound professional and business-oriented
    8. Add acceptance criteria and evaluation process
    9. Include contact information and proposal submission guidelines

    Focus on creating a comprehensive PRD that clearly outlines what the client needs and what kind of development team they're looking for.

    IMPORTANT: Return ONLY the RFP content in markdown format. Do NOT include any code block markers like ```markdown or ``` in your response.
  """)

  response = openai_clinet.responses.create(
    model=generator_model, input=prompt, temperature=0.7
  )
  content = response.output_text

  content = content.replace("```markdown", "").replace("```", "")
  content = content.strip()

  if not content:
    raise ValueError(f"LLM returned empty content for RFP {rfp['id']}")

  return content


def generate_rfps(
  num_rfps: int,
  rfps_dir: Path,
  openai_clinet: OpenAI,
  generator_model: str,
  faker: Faker,
):
  print(f"Generating {num_rfps} RFP records and PDFs...")
  rfps: list[dict] = generate_rfps_data_dicts(num_rfps, faker)

  generated_rfp_files = []
  for i, rfp in enumerate(rfps, 1):
    print(f"Generating RFP PDF {i}/{num_rfps}: {rfp['title']}")

    rfp_markdown = generate_rfp_markdown(rfp, openai_clinet, generator_model)

    safe_title = rfp["title"].replace(" ", "_").replace(".", "").replace("/", "_")
    filename = f"rfp_{rfp['id']}_{safe_title}"

    file_path = save_markdown_as_pdf(rfp_markdown, filename, rfps_dir)
    generated_rfp_files.append(file_path)


def main():
  num_rfps = 2
  rfps_dir = Path("data/RFP")
  generator_model = "gpt-4o-mini"

  load_dotenv(override=True)

  api_key = os.getenv("OPENAI_API_KEY")
  if api_key is None:
    raise RuntimeError("OPENAI_API_KEY is not set in .env")

  client = OpenAI()

  faker = Faker()

  generate_rfps(num_rfps, rfps_dir, client, generator_model, faker)


if __name__ == "__main__":
  main()
