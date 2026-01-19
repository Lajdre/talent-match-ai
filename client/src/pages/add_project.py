import httpx
import streamlit as st

from api.client import upload_projects
from utils.utils import set_backgroud


def render():
  set_backgroud()
  st.title("➕ Add Projects")

  st.markdown("Upload a **projects JSON file** to import projects into the system.")

  uploaded_file = st.file_uploader(
    "Choose a projects file",
    type=["json"],
    help="Upload a JSON file containing project definitions",
  )

  if uploaded_file is not None:
    st.info(f"📄 **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

    with st.expander("Preview file contents"):
      try:
        content = uploaded_file.getvalue().decode("utf-8")
        st.code(
          content[:2000] + ("..." if len(content) > 2000 else ""), language="json"
        )
      except Exception:
        st.warning("Could not preview file contents")

    if st.button("Import Projects", type="primary"):
      with st.spinner("Processing projects file..."):
        try:
          result = upload_projects(uploaded_file.name, uploaded_file.getvalue())
          st.success("✅ Projects imported successfully!")

          st.subheader("Ingestion Result")
          st.json(result)

        except httpx.HTTPStatusError as e:
          st.error(f"API Error: {e.response.status_code}")
          try:
            detail = e.response.json().get("detail", str(e))
          except Exception:
            detail = e.response.text
          st.code(detail)
        except httpx.RequestError as e:
          st.error(f"Connection error: {e}")


render()
