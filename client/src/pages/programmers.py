import streamlit as st

from api.client import get_programmers
from utils.utils import set_backgroud


def render():
  set_backgroud()
  st.title("💻 Programmers")

  status_filter = st.selectbox(
    "Filter by status",
    options=[None, "available", "assigned"],
    format_func=lambda x: "All" if x is None else x.capitalize(),
  )

  try:
    programmers = get_programmers(status_filter)
  except Exception as e:
    st.error(f"Failed to fetch programmers: {e}")
    return

  if not programmers:
    st.info("No programmers found.")
    return

  n_programmers = len(programmers)
  st.markdown(f"**{n_programmers}** programmer{'s' if n_programmers > 1 else ''} found")

  for prog in programmers:
    print(prog)
    with st.container(border=True):
      col1, col2 = st.columns([3, 1])

      with col1:
        st.subheader(prog["id"])

        if any(prog["skills"].values()):
          st.caption(_format_skills(prog["skills"]))

      with col2:
        if prog["is_assigned"]:
          st.success("Assigned")
          if prog["current_project"]:
            st.caption(f"📁 {prog['current_project']}")
        else:
          st.warning("Available")


def _format_skills(skills: dict[str, list[str]]) -> str:
  order = ["Expert", "Advanced", "Intermediate", "Beginner"]
  parts = []

  for level in order:
    if skills.get(level):
      skill_list = ", ".join(skills[level])
      parts.append(f"**{level}:** {skill_list}")

  return "   ".join(parts)


render()
