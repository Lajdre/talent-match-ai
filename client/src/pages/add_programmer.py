import httpx
import streamlit as st

from api.client import upload_cv
from utils.utils import set_backgroud


def render():
  set_backgroud()
  st.title("➕ Add Programmer")

  st.markdown("Upload a programmer's **CV (PDF)** to extract their information.")

  uploaded_file = st.file_uploader(
    "Choose a CV file",
    type=["pdf"],
    help="Upload a PDF file containing the programmer's CV",
  )

  if uploaded_file is not None:
    st.info(f"📄 **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

    if st.button("Process CV", type="primary"):
      with st.spinner("Processing CV... This may take a moment."):
        try:
          result = upload_cv(uploaded_file.name, uploaded_file.getvalue())
          st.success("✅ CV processed successfully!")

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
