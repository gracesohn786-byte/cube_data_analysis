"""Figures 8 and 10: prior activities and Q15 hope-to-gain themes."""

import streamlit as st

from lib.loaders import load_activity_summary, load_theme_frequency
from lib.ui import render_disclaimer, render_figure

st.title("Activities and themes")
st.write(
    "Prior course activities (Q5/Q6) and themes in what students hoped to gain "
    "(Q15). Open-ended response text is not shown."
)

render_figure(8)

st.subheader("Activity summary table")
try:
    activities = load_activity_summary()
    st.dataframe(activities, width="stretch", hide_index=True)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load activity summary: {exc}")

st.divider()
render_figure(10)

st.subheader("Theme frequency table")
st.caption(
    "Multi-label keyword-assisted themes. Percentages can exceed 100% in total. "
    "Raw Q15 text and assignment files are restricted and omitted here."
)
try:
    themes = load_theme_frequency()
    st.dataframe(themes, width="stretch", hide_index=True)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load theme frequency: {exc}")

render_disclaimer()
