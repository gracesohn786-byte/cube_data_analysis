"""Cached, privacy-safe loaders for non-restricted analysis outputs."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib.paths import Survey, output_csv

PRE_ALLOWED_CSVS = frozenset(
    {
        "variable_inventory.csv",
        "descriptive_statistics.csv",
        "group_and_wave_summary.csv",
        "skill_summary.csv",
        "scale_reliability.csv",
        "respondent_block_means.csv",
        "correlations.csv",
        "predictor_model_summary.csv",
        "predictor_model_diagnostics.csv",
        "q5_q6_activity_summary.csv",
        "q15_theme_codebook.csv",
        "q15_theme_frequency.csv",
        "validation_results.csv",
    }
)

POST_ALLOWED_CSVS = frozenset(
    {
        "variable_inventory.csv",
        "descriptive_statistics.csv",
        "group_and_wave_summary.csv",
        "skill_summary.csv",
        "scale_reliability.csv",
        "respondent_block_means.csv",
        "correlations.csv",
        "q5_q6_activity_summary.csv",
        "q15_theme_codebook.csv",
        "q15_theme_frequency.csv",
        "other_text_normalization.csv",
        "validation_results.csv",
    }
)

ALLOWED_BY_SURVEY = {
    "pre": PRE_ALLOWED_CSVS,
    "post": POST_ALLOWED_CSVS,
}

# Backward-compatible alias for pre-survey callers.
ALLOWED_CSVS = PRE_ALLOWED_CSVS


@st.cache_data(show_spinner=False)
def load_csv(filename: str, survey: Survey = "pre") -> pd.DataFrame:
    allowed = ALLOWED_BY_SURVEY[survey]
    if filename not in allowed:
        raise PermissionError(
            f"CSV '{filename}' is not on the {survey}-survey allowlist. "
            "Restricted or unapproved files cannot be loaded."
        )
    return pd.read_csv(output_csv(filename, survey=survey))


@st.cache_data(show_spinner=False)
def load_predictor_summary() -> pd.DataFrame:
    df = load_csv("predictor_model_summary.csv", survey="pre")
    display = df.loc[df["term"] != "const"].copy()
    cols = [
        "model",
        "n",
        "r_squared",
        "term_label",
        "standardized_beta",
        "standardized_ci95_low",
        "standardized_ci95_high",
        "standardized_p_value",
    ]
    return display[cols].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_key_correlations(survey: Survey = "pre") -> pd.DataFrame:
    return load_csv("correlations.csv", survey=survey)


@st.cache_data(show_spinner=False)
def load_theme_frequency(survey: Survey = "pre") -> pd.DataFrame:
    return load_csv("q15_theme_frequency.csv", survey=survey)


@st.cache_data(show_spinner=False)
def load_activity_summary(survey: Survey = "pre") -> pd.DataFrame:
    return load_csv("q5_q6_activity_summary.csv", survey=survey)


@st.cache_data(show_spinner=False)
def load_variable_inventory(survey: Survey = "pre") -> pd.DataFrame:
    return load_csv("variable_inventory.csv", survey=survey)
