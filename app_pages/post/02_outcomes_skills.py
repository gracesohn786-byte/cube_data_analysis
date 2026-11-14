"""Post-survey Figures 1–2: response patterns and skill ratings."""

import streamlit as st

from lib.ui import render_disclaimer, render_figure

st.title("Outcomes and skills")
st.write(
    "Overall ordered-response patterns and the nine-skill profile after the "
    "CUBEs project."
)

render_figure(1, survey="post")
st.divider()
render_figure(2, survey="post")
render_disclaimer(survey="post")
