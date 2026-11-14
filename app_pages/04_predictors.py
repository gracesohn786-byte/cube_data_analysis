"""Figures 4–7: simple two-predictor models."""

import streamlit as st

from lib.loaders import load_predictor_summary
from lib.ui import render_disclaimer, render_figure

st.title("Predictor models")
st.write(
    "Prespecified two-predictor associations for workforce readiness, "
    "coursework preparedness, and CUBEs excitement. Results describe "
    "associations, not causal effects."
)

render_figure(4)
st.divider()
render_figure(5)
st.divider()
render_figure(6)
st.divider()
render_figure(7)

st.subheader("Model summary")
st.caption(
    "Standardized coefficients from the simple two-predictor OLS models "
    "(HC3 robust intervals)."
)
try:
    summary = load_predictor_summary()
    display = summary.copy()
    display["r_squared"] = display["r_squared"].round(3)
    display["standardized_beta"] = display["standardized_beta"].round(3)
    display["standardized_ci95_low"] = display["standardized_ci95_low"].round(3)
    display["standardized_ci95_high"] = display["standardized_ci95_high"].round(3)
    display = display.rename(
        columns={
            "model": "Model",
            "n": "n",
            "r_squared": "R²",
            "term_label": "Predictor",
            "standardized_beta": "Std. β",
            "standardized_ci95_low": "95% CI low",
            "standardized_ci95_high": "95% CI high",
            "standardized_p_value": "p",
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load predictor summary: {exc}")

render_disclaimer()
