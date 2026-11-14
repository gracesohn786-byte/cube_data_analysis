"""CUBEs survey analysis — Streamlit entrypoint (pre- and post-survey)."""

import streamlit as st

st.set_page_config(
    page_title="CUBEs survey analysis",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = {
    "Pre-survey": [
        st.Page(
            "app_pages/00_home.py",
            title="Overview",
            icon=":material/home:",
            default=True,
        ),
        st.Page(
            "app_pages/01_data_methods.py",
            title="Data and methods",
            icon=":material/database:",
            url_path="pre-data-methods",
        ),
        st.Page(
            "app_pages/02_outcomes_skills.py",
            title="Outcomes and skills",
            icon=":material/bar_chart:",
            url_path="pre-outcomes-skills",
        ),
        st.Page(
            "app_pages/03_associations.py",
            title="Associations",
            icon=":material/grid_on:",
            url_path="pre-associations",
        ),
        st.Page(
            "app_pages/04_predictors.py",
            title="Predictor models",
            icon=":material/trending_up:",
            url_path="pre-predictors",
        ),
        st.Page(
            "app_pages/05_activities_themes.py",
            title="Activities and themes",
            icon=":material/category:",
            url_path="pre-activities-themes",
        ),
        st.Page(
            "app_pages/06_trends_quality.py",
            title="Trends and quality",
            icon=":material/timeline:",
            url_path="pre-trends-quality",
        ),
    ],
    "Post-survey": [
        st.Page(
            "app_pages/post/00_home.py",
            title="Overview",
            icon=":material/home:",
            url_path="post-overview",
        ),
        st.Page(
            "app_pages/post/01_data_methods.py",
            title="Data and methods",
            icon=":material/database:",
            url_path="post-data-methods",
        ),
        st.Page(
            "app_pages/post/02_outcomes_skills.py",
            title="Outcomes and skills",
            icon=":material/bar_chart:",
            url_path="post-outcomes-skills",
        ),
        st.Page(
            "app_pages/post/03_associations.py",
            title="Associations",
            icon=":material/grid_on:",
            url_path="post-associations",
        ),
        st.Page(
            "app_pages/post/04_enjoyment_benefit.py",
            title="Enjoyment and benefit",
            icon=":material/favorite:",
            url_path="post-enjoyment-benefit",
        ),
        st.Page(
            "app_pages/post/05_activities_themes.py",
            title="Activities and themes",
            icon=":material/category:",
            url_path="post-activities-themes",
        ),
        st.Page(
            "app_pages/post/06_trends_quality.py",
            title="Trends and quality",
            icon=":material/timeline:",
            url_path="post-trends-quality",
        ),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
