import base64

import streamlit as st


def _get_img_as_base64(file) -> str:
  with open(file, "rb") as f:
    data = f.read()
  return base64.b64encode(data).decode()


def _get_page_bg_data() -> str:
  return f"""
  <style>
  [data-testid="stHeader"]{{
      background-color: rgba(0,0,0,0);
  }}

  [data-testid="stAppViewContainer"]{{
      background-image: url("data:image/png;base64,{_get_img_as_base64("./assets/output.jpg")}");
      background-size: cover;
  }}

  [data-testid="stSidebar"]> div:first-child{{
    background-image: url("data:image/png;base64,{_get_img_as_base64("./assets/dark_bg.jpg")}");
    background-size: cover;
  }}
  </style>
  """


def set_backgroud() -> None:
  st.markdown(_get_page_bg_data(), unsafe_allow_html=True)
