"""Post-survey Figures 6 and 8: wave trends and missingness."""

import streamlit as st

from lib.ui import render_disclaimer, render_figure

st.title("Trends and quality")
st.write(
    "Year-to-year descriptive patterns for key measures, plus missingness "
    "driven by survey versions and branching."
)

render_figure(6, survey="post")
st.divider()
render_figure(8, survey="post")
render_disclaimer(survey="post")
