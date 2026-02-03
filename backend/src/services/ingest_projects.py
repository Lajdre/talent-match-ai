import json
import logging
from pathlib import Path
from typing import Any

import aiofiles

from core.models.project_models import ProjectStructure
from repositories.project_repository import upsert_project

logger = logging.getLogger(__name__)


async def process_projects_json(path: Path) -> dict[str, Any]:
  """
  Reads projects.json, validates it against Pydantic models,
  and persists to Neo4j via ProjectRepository.
  """
  try:
    if not path.exists():
      raise FileNotFoundError(f"Projects file not found at {path}")

    async with aiofiles.open(path, "r") as f:
      raw_data = json.loads(await f.read())

    processed_count = 0
    errors = []

    for item in raw_data:
      try:
        project = ProjectStructure(**item)

        upsert_project(project)
        processed_count += 1

      except Exception as e:
        logger.error(f"Failed to process project {item.get('id', 'unknown')}: {e}")
        errors.append(f"ID {item.get('id')}: {str(e)}")

    return {
      "status": "success",
      "processed": processed_count,
      "total_in_file": len(raw_data),
      "errors": errors,
    }

  except Exception as e:
    logger.error(f"Global project ingestion failed: {e}")
    raise RuntimeError(str(e)) from None
