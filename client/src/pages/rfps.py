import streamlit as st

from api.client import get_rfps
from utils.utils import set_backgroud


def _skill_badge(skill: dict) -> str:
  level = skill.get("level", "")
  mandatory = skill.get("mandatory", False)
  name = skill.get("name", "Unknown")
  icon = "🔴" if mandatory else "⚪"
  return f"{icon} {name} ({level})"


def render():
  set_backgroud()
  st.title("📋 RFPs")

  try:
    rfps = get_rfps()
  except Exception as e:
    st.error(f"Failed to fetch RFPs: {e}")
    return

  if not rfps:
    st.info("No RFPs found.")
    return

  st.markdown(f"**{len(rfps)}** RFP(s) found")

  for rfp in rfps:
    with st.container(border=True):
      title = rfp.get("title") or rfp["id"]
      st.subheader(title)

      col1, col2 = st.columns(2)
      with col1:
        st.caption(f"**ID:** {rfp['id']}")
        if rfp.get("client"):
          st.caption(f"**Client:** {rfp['client']}")
      with col2:
        if rfp.get("budget"):
          st.caption(f"**Budget:** {rfp['budget']}")

      needed_skills = rfp.get("needed_skills", [])
      if needed_skills:
        st.markdown("**Required Skills:**")
        mandatory = [s for s in needed_skills if s.get("mandatory")]
        optional = [s for s in needed_skills if not s.get("mandatory")]

        if mandatory:
          st.markdown("Mandatory: " + " • ".join(_skill_badge(s) for s in mandatory))
        if optional:
          st.markdown("Optional: " + " • ".join(_skill_badge(s) for s in optional))


render()
