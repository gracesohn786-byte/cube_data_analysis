"""Figure 3: relationships among pre-survey measures."""

import streamlit as st

from lib.loaders import load_key_correlations
from lib.ui import render_disclaimer, render_figure

st.title("Associations")
st.write(
    "Spearman correlations among pre-survey measures. Larger positive values "
    "mean higher ratings tend to occur together."
)

render_figure(3)

st.subheader("Correlation table")
st.caption("Pairs from the analysis output (non-restricted).")
try:
    corr = load_key_correlations()
    st.dataframe(corr, width="stretch", hide_index=True)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load correlations: {exc}")

render_disclaimer()
