"""Post-survey Figure 4: project enjoyment and CUBEs benefit."""

import streamlit as st

from lib.ui import render_disclaimer, render_figure

st.title("Enjoyment and benefit")
st.write(
    "Joint distribution of project enjoyment and perceived CUBEs benefit "
    "ratings."
)

render_figure(4, survey="post")
render_disclaimer(survey="post")
