"""Report-backed interpretation copy for the post-survey Streamlit app.

Primary source: post_survey/Post_Survey_report.docx
Fallback for denominators/limitations: analysis_output/FIGURE_GUIDE.md and README.md
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class FigureContent(TypedDict):
    id: int
    title: str
    image: str
    summary: str
    bullets: list[str]
    note: str | None
    note_kind: str  # "info" | "warning" | "caption"
    questions: NotRequired[list[str]]


SCOPE = {
    "title": "CUBEs post-survey analysis",
    "blurb": (
        "This report shows visualizations and interpretations of CUBEs "
        "post-project survey data, covering response patterns, skills, "
        "project enjoyment and benefit, prior activities, themes in what "
        "students gained, wave trends, and data quality."
    ),
    "respondent_rows": 345,
    "primary_n": 280,
    "q15_n": 237,
    "years": "2022–2026",
}

OVERALL_TAKEAWAYS = [
    (
        "Students generally identified CUBEs real-world project to be beneficial. "
        "Additionally, benefit ratings had positive correlation with enjoyment ratings."
    ),
    (
        "Students gave high career benefit ratings for all nine skills. Teamwork was "
        "the leading skill in proficiency and career benefit, while research and "
        "teamwork were for reported improvement."
    ),
    (
        "The open-ended responses reflect the numeric results (ratings on scale). "
        "Students frequently talked about learning, business knowledge, research or "
        "data skills, and real-world experience."
    ),
    (
        "Prior real-organization projects and business plans received especially "
        "strong ratings on career benefit among students who did them."
    ),
    (
        "Networking appears to be a weaker area than most other outcomes and may be "
        "worth drawing extra attention."
    ),
]

DISCLAIMER = (
    "Results describe cross-sectional associations, not causal effects. "
    "Q15 themes are exploratory, keyword-assisted, and multi-label. "
    "Q3 and Q6 include structural missingness from survey versions and branching. "
    "Seven Q14 responses with unlabeled code 41 were excluded. "
    "Restricted open-ended text is not shown."
)

DATA_METHODS = {
    "intro_bullets": [
        "The cleaned post-survey dataset contains 345 respondent rows from 2022 through 2026.",
        "Most quantitative figures use the recommended analytic sample of 280 sufficiently complete responses (recommended_include=True).",
        "The open-ended theme chart uses all 237 nonblank responses to Q15.",
        "The figures describe patterns in these survey responses. They do not by themselves show that the CUBEs project caused an outcome.",
    ],
    "limitations": [
        "Q10–Q13 numeric anchors are absent from the export and should be confirmed.",
        "Seven Q14 responses were stored as the unlabeled code 41 and were excluded from ordinal calculations.",
        "Q18 contains many unmapped numeric class codes, so class-level comparisons are not produced.",
        "Q3 and Q6 contain expected structural missingness from survey versions and branching.",
        "Q15 theme assignments are exploratory, multi-label, and keyword-assisted; double-coding is recommended before formal reporting.",
        "Wave and subgroup patterns may reflect who responded, which courses participated, or small sample sizes—not causal trends.",
    ],
}

FIGURES: dict[int, FigureContent] = {
    1: {
        "id": 1,
        "title": "Figure 1. Overall response patterns",
        "image": "ordinal_distributions.png",
        "summary": (
            "This chart summarizes five survey questions that use ordered response "
            "choices. Bars extending farther to the right represent more positive "
            "or more frequent responses."
        ),
        "bullets": [
            "Most students said the CUBEs real-world project was beneficial. The largest portion of the bar falls in the two positive response categories.",
            "Students also tended to report being prepared by their coursework and somewhat ready for the workforce.",
            "Networking opportunities had more mixed responses. Many students reported networking “seldom” or “sometimes”, while fewer selected the two most frequent categories.",
        ],
        "questions": ["Q14", "Q9", "Q8", "Q7", "Q4"],
        "note": (
            "The questions do not all use the same wording or number of response "
            "choices. Each bar represents a pattern within that question, not the "
            "exact bar lengths as if all five scales were identical."
        ),
        "note_kind": "warning",
    },
    2: {
        "id": 2,
        "title": "Figure 2. Skill ratings",
        "image": "skill_profile.png",
        "summary": (
            "This figure compares ratings in three categories—students’ current "
            "proficiency, how beneficial each skill is for a career, and how much "
            "students felt they improved—for the nine skills listed on the y-axis."
        ),
        "bullets": [
            "Teamwork received the highest average current-proficiency rating (4.26 out of 5) and the highest career-benefit rating (4.44).",
            "Students reported the greatest improvement in research (3.77) and teamwork (3.76). Public speaking was close behind (3.68).",
            "Professional writing had the lowest reported improvement (3.27).",
            "Public speaking and data analysis had the lowest current-proficiency ratings (both about 3.4), suggesting that these areas may need additional support.",
            "For every skill, the career-benefit rating was relatively high. Students generally saw the skills as useful even when they rated their current ability or improvement lower.",
        ],
        "questions": ["Q10", "Q11", "Q12"],
        "note": (
            "The original export contains numeric values but not the full written "
            "scale anchors. These means should be interpreted as relative "
            "comparisons until the 0–5 anchors are confirmed."
        ),
        "note_kind": "info",
    },
    3: {
        "id": 3,
        "title": "Figure 3. Relationships among survey measures",
        "image": "construct_correlation_heatmap.png",
        "summary": (
            "The heatmap shows correlations between survey measures. A value closer "
            "to 1 means that students gave high ratings for the two corresponding "
            "measures. The statistic shown is Spearman’s rho, a measure of "
            "association based on response order."
        ),
        "bullets": [
            "The strongest relationship is between students’ skill proficiency and how beneficial they believe those skills are for their careers (rho = 0.69).",
            "Project enjoyment and perceived CUBEs benefit are also strongly related (rho = 0.63). Students who enjoyed the project more generally found it more beneficial.",
            "Reported improvement is moderately related to career benefit (0.52), proficiency (0.50), and enjoyment (0.45).",
            "Networking frequency has weak relationships with most other measures. It appears to capture something different from project enjoyment, benefit, and skill growth.",
        ],
        "note": (
            "This graph shows a correlation between the survey measures, not cause "
            "and effect. For example, this figure does not prove that enjoyment "
            "caused students to see more benefit, or vice versa."
        ),
        "note_kind": "warning",
    },
    4: {
        "id": 4,
        "title": "Figure 4. Project enjoyment and CUBEs benefit",
        "image": "enjoyment_by_benefit_heatmap.png",
        "summary": (
            "This heatmap shows the count of students for each combination of "
            "project-enjoyment and CUBEs-benefit ratings. Darker cells contain more "
            "respondents."
        ),
        "bullets": [
            "Responses are concentrated in the lower-right corner, where both enjoyment and perceived benefit are high.",
            "Among the 255 students with both measures available, 102 selected the highest value on both enjoyment and benefit.",
            "Another 40 students selected the highest benefit category and the second-highest enjoyment rating. Very few students gave low ratings on both measures.",
            "Q14 ordinal codes in the export: 0 = Very unbeneficial, 1 = Somewhat unbeneficial, 2 = unlabeled code 41 (treating as “Neutral” is questionable), 3 = Somewhat beneficial, 4 = Very beneficial. Q13: higher enjoyment with increasing score.",
        ],
        "note": (
            "Seven Q14 responses were excluded. The missing middle row reflects the "
            "absent Q14 midpoint label."
        ),
        "note_kind": "warning",
    },
    5: {
        "id": 5,
        "title": "Figure 5. Prior activities and career contribution",
        "image": "q5_selection_q6_contribution.png",
        "summary": (
            "The left panel shows how often students selected each type of prior "
            "course activity. The right panel shows how strongly students who "
            "selected that activity felt it contributed to career preparation."
        ),
        "bullets": [
            "Research projects were the most common prior activity, selected by 77% of the 257 students who answered Q5. Case studies were next at 61%.",
            "Real business or organization projects received the highest average contribution rating (3.19 out of 4), even though they were less common than research projects and case studies.",
            "Business plans also received a high contribution rating (3.02). Case studies had the lowest average among the four main activities (2.45), though the typical response still fell around the middle-to-positive range.",
        ],
        "note": (
            "The ratings are obtained from the pool of students who selected an "
            "activity. They do not prove that one activity caused better outcomes "
            "in general. Q6 missingness mostly reflects survey branching."
        ),
        "note_kind": "warning",
    },
    6: {
        "id": 6,
        "title": "Figure 6. Patterns across survey years",
        "image": "wave_trends.png",
        "summary": (
            "The linear time-series plots show average ratings for six different "
            "measures from 2022 through 2026."
        ),
        "bullets": [
            "Reported skill improvement and perceived CUBEs benefit are higher in the more recent years, especially 2025 and 2026.",
            "Average networking frequency shows a downward trend across the years.",
            "Workforce-readiness ratings rose gradually through 2025 and then dropped in 2026.",
            "Course-preparedness ratings show significant variations rather than following one steady trend.",
            "Mean proficiency changed moderately overall, with a small increase in 2025 and 2026.",
        ],
        "note": (
            "The 2026 recommended sample contains only 25 students, so its averages "
            "can move more easily than averages from larger years. The groups may "
            "also differ by course or class. These lines are descriptive and do not "
            "provide hard evidence of improvement or decline over time."
        ),
        "note_kind": "warning",
    },
    7: {
        "id": 7,
        "title": "Figure 7. Themes in what students gained",
        "image": "q15_theme_frequency.png",
        "summary": (
            "This chart summarizes themes found in 237 nonblank answers to "
            "“What did you gain from this course?” A response could receive more "
            "than one theme."
        ),
        "bullets": [
            "Knowledge or conceptual understanding was the most common theme, appearing in 112 responses (47.3%).",
            "Business, marketing, or management appeared in 78 responses (32.9%), while research, data, or analytics appeared in 62 (26.2%).",
            "Applied or real-world experience appeared in 51 responses (21.5%).",
            "Communication, teamwork, problem-solving, and career readiness were also recurring takeaways.",
            "The range of themes suggests that students gained both subject knowledge and broader workplace skills rather than one single thing.",
        ],
        "questions": ["Q15"],
        "note": (
            "Themes were assigned with transparent keyword-assisted rules and "
            "required human review. Because coding is multi-label, percentages add "
            "to more than 100%. The chart should be treated as an exploratory "
            "summary rather than confirmation. Original open-ended text is not "
            "shown in this app."
        ),
        "note_kind": "info",
    },
    8: {
        "id": 8,
        "title": "Figure 8. Missing data and survey structure",
        "image": "missingness_quality.png",
        "summary": (
            "This figure shows the percentage of respondent rows missing each key "
            "variable. Orange bars identify questions whose missingness mainly "
            "comes from survey versions or branching."
        ),
        "bullets": [
            "Q6 activity-contribution data has the largest number of missing rows, ranging from about 37% to 62%. This may be because respondents were asked only about activities that applied to them.",
            "Q3 is missing about 52% of rows because it was absent from earlier survey versions and was asked only of respondents who were working.",
            "The open-ended Q15 question is blank for 31% of rows. Core outcomes such as readiness, preparedness, networking, and qualifications have lower missingness, generally about 9% to 10%.",
        ],
        "note": (
            "High missingness does not always mean poor data quality. Q3 and Q6 "
            "require special handling because many blank cells are expected by "
            "design. They should not be filled with zeros or combined with ordinary "
            "nonresponse."
        ),
        "note_kind": "warning",
    },
}
