"""Data overview, denominators, and analysis limitations."""

import streamlit as st

from lib.content import DATA_METHODS, SCOPE
from lib.loaders import load_variable_inventory
from lib.ui import render_disclaimer

st.title("Data and methods")
st.write(
    "The cleaned pre-survey dataset contains "
    f"**{SCOPE['respondent_rows']}** respondent rows from **{SCOPE['years']}**."
)

st.subheader("Scope and denominators")
for bullet in DATA_METHODS["intro_bullets"]:
    st.markdown(f"- {bullet}")

st.subheader("Three focal outcomes")
st.markdown(
    """
- **Workforce readiness** (Q4)
- **Coursework preparedness** (Q7)
- **CUBEs excitement** (Q14)
"""
)

st.subheader("Important limitations")
for item in DATA_METHODS["limitations"]:
    st.markdown(f"- {item}")

st.subheader("Variable inventory")
st.caption(
    "Summary of key analysis variables from the cleaned pre-survey outputs. "
    "Restricted identifiers and open-ended text are excluded from this app."
)
try:
    inventory = load_variable_inventory()
    st.dataframe(inventory, width="stretch", hide_index=True)
except Exception as exc:  # noqa: BLE001 — show a friendly load error
    st.error(f"Could not load variable inventory: {exc}")

render_disclaimer()
