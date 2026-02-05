import logging
from pathlib import Path

from unstructured.partition.pdf import partition_pdf

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> str:
  """Extract text content from a PDF file using unstructured.

  Shared utility for CVs and RFPs.
  """
  try:
    elements = partition_pdf(filename=str(pdf_path))
    return "\n\n".join([str(element) for element in elements])
  except Exception as e:
    logger.exception("Failed to extract text from %s.", pdf_path)
    raise ValueError(f"Could not extract text from PDF: {e}") from None
