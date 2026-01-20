import streamlit as st

from api.client import get_projects
from utils.utils import set_backgroud


def _status_color(status: str | None) -> str:
  if status == "active":
    return "🟢"
  if status == "completed":
    return "✅"
  return "⚪"


def render():
  set_backgroud()
  st.title("📁 Projects")

  try:
    projects = get_projects()
  except Exception as e:
    st.error(f"Failed to fetch projects: {e}")
    return

  if not projects:
    st.info("No projects found.")
    return

  st.markdown(f"**{len(projects)}** project(s) found")

  for proj in projects:
    with st.container(border=True):
      status = proj.get("status")
      title = proj.get("title") or proj["id"]

      st.subheader(f"{_status_color(status)} {title}")

      col1, col2 = st.columns(2)
      with col1:
        st.caption(f"**ID:** {proj['id']}")
        if proj.get("client"):
          st.caption(f"**Client:** {proj['client']}")
      with col2:
        if status:
          st.caption(f"**Status:** {status.capitalize()}")

      if proj.get("description"):
        st.markdown(proj["description"])

      if proj.get("required_skills"):
        st.markdown("**Required Skills:** " + ", ".join(proj["required_skills"]))

      team = proj.get("assigned_team", [])
      team_ids = [m["id"] for m in team if m.get("id")]
      if team_ids:
        st.markdown("**Team:** " + ", ".join(team_ids))


render()
