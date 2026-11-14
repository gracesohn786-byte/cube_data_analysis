"""Shared Streamlit UI helpers for figure presentation."""

from __future__ import annotations

from typing import Any

import streamlit as st

from lib.paths import Survey, figure_path


def _figures_for(survey: Survey) -> dict[int, Any]:
    if survey == "pre":
        from lib.content import FIGURES

        return FIGURES
    from lib.post_content import FIGURES

    return FIGURES


def _disclaimer_for(survey: Survey) -> str:
    if survey == "pre":
        from lib.content import DISCLAIMER

        return DISCLAIMER
    from lib.post_content import DISCLAIMER

    return DISCLAIMER


def render_disclaimer(survey: Survey = "pre") -> None:
    st.caption(_disclaimer_for(survey))


def render_figure(fig_id: int, survey: Survey = "pre") -> None:
    fig = _figures_for(survey)[fig_id]
    st.subheader(fig["title"])
    st.image(
        str(figure_path(fig["image"], survey=survey)),
        width="stretch",
        alt=fig["title"],
    )
    st.markdown(f"**Summary.** {fig['summary']}")
    questions = fig.get("questions")
    if questions:
        st.caption("Questions analyzed: " + ", ".join(questions))
    with st.expander("Notable features", expanded=True):
        for bullet in fig["bullets"]:
            st.markdown(f"- {bullet}")
    note = fig.get("note")
    if note:
        kind = fig.get("note_kind") or "info"
        if kind == "warning":
            st.warning(note, icon=":material/warning:")
        elif kind == "info":
            st.info(note, icon=":material/info:")
        else:
            st.caption(note)
