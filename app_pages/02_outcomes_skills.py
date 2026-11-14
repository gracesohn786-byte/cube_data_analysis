"""Figures 1–2: response patterns and skill profile."""

import streamlit as st

from lib.ui import render_disclaimer, render_figure

st.title("Outcomes and skills")
st.write(
    "Baseline distributions for the focal outcomes and the nine-skill profile "
    "before the CUBEs project."
)

render_figure(1)
st.divider()
render_figure(2)
render_disclaimer()
