from pathlib import Path

import markdown
from weasyprint import CSS, HTML


def save_markdown_as_pdf(
  markdown_content: str, filename: str, output_dir: Path
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)

  html_content = markdown.markdown(markdown_content)

  css_content = """
    body {
        font-family: Arial, sans-serif;
        line-height: 1.6;
        max-width: 800px;
        margin: 40px auto;
        padding: 20px;
    }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
    h2 { color: #34495e; margin-top: 30px; }
    h3 { color: #7f8c8d; }
    strong { color: #2c3e50; }
    ul { margin-left: 20px; }
   """

  pdf_path = output_dir / f"{filename}.pdf"
  HTML(string=html_content).write_pdf(pdf_path, stylesheets=[CSS(string=css_content)])

  return pdf_path
