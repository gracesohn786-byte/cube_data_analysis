"""Resolve analysis-output paths for pre- and post-survey Streamlit pages."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

Survey = Literal["pre", "post"]

ROOT = Path(__file__).resolve().parent.parent

_SURVEY_ROOTS = {
    "pre": ROOT / "pre_survey" / "analysis_output",
    "post": ROOT / "post_survey" / "analysis_output",
}


def analysis_root(survey: Survey = "pre") -> Path:
    return _SURVEY_ROOTS[survey]


def figures_dir(survey: Survey = "pre") -> Path:
    return analysis_root(survey) / "figures"


def outputs_dir(survey: Survey = "pre") -> Path:
    # Pre CSVs live under outputs/; post CSVs are at analysis_output root.
    if survey == "pre":
        return analysis_root(survey) / "outputs"
    return analysis_root(survey)


def figure_path(filename: str, survey: Survey = "pre") -> Path:
    path = figures_dir(survey) / filename
    if not path.is_file():
        raise FileNotFoundError(f"Figure not found: {path}")
    return path


def output_csv(filename: str, survey: Survey = "pre") -> Path:
    if "RESTRICTED" in filename.upper():
        raise PermissionError(f"Restricted file blocked: {filename}")
    path = outputs_dir(survey) / filename
    if not path.is_file():
        raise FileNotFoundError(f"Output CSV not found: {path}")
    return path


# Backward-compatible aliases used by older pre-only imports.
PRE_SURVEY = ROOT / "pre_survey"
ANALYSIS_OUTPUT = _SURVEY_ROOTS["pre"]
FIGURES_DIR = figures_dir("pre")
OUTPUTS_DIR = outputs_dir("pre")
