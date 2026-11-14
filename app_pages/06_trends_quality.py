"""Figures 9 and 11: wave trends and missingness / survey structure."""

import streamlit as st

from lib.ui import render_disclaimer, render_figure

st.title("Trends and quality")
st.write(
    "Year-to-year descriptive patterns for the three outcomes, plus missingness "
    "driven by survey versions and branching."
)

render_figure(9)
st.divider()
render_figure(11)
render_disclaimer()
