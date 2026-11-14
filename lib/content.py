"""Report-backed interpretation copy for the pre-survey Streamlit app.

Primary source: pre_survey/Pre_Survey_report.docx
Fallback clarity: pre_survey/analysis_output/PRE_SURVEY_FIGURE_GUIDE.md
"""

from __future__ import annotations

from typing import TypedDict


class FigureContent(TypedDict):
    id: int
    title: str
    image: str
    summary: str
    bullets: list[str]
    note: str | None
    note_kind: str  # "info" | "warning" | "caption"


SCOPE = {
    "title": "CUBEs pre-survey analysis",
    "blurb": (
        "This report shows visualizations and interpretations of CUBEs "
        "pre-project survey data. It focuses on the three selected outcomes: "
        "workforce readiness, coursework preparedness, and CUBEs excitement."
    ),
    "respondent_rows": 447,
    "primary_n": 367,
    "q15_n": 341,
    "years": "2022–2026",
}

OVERALL_TAKEAWAYS = [
    (
        "Workforce readiness is most clearly related to students’ view of their "
        "job qualifications followed by their current skill proficiency."
    ),
    (
        "Coursework preparedness is related to workforce readiness, but the two "
        "are not interchangeable; the simple model explains only part of the variation."
    ),
    (
        "CUBEs excitement shows strong correlation to ratings on looking forward "
        "to the project and is largely separate from workforce readiness."
    ),
    (
        "Students see all nine skills as career-relevant, with especially large "
        "perceived growth opportunities in research and data analysis."
    ),
    (
        "Students most often hoped to gain knowledge, business understanding, "
        "real-world experience, and research or data skills."
    ),
]

DISCLAIMER = (
    "Results describe cross-sectional associations, not causal effects. "
    "Q15 themes are exploratory, keyword-assisted, and multi-label. "
    "Q6 results describe a small recent subset and should not be generalized "
    "to the full pre-survey sample. Restricted open-ended text is not shown."
)

DATA_METHODS = {
    "intro_bullets": [
        "The cleaned pre-survey dataset contains 447 respondent rows from 2022 through 2026.",
        "Primary quantitative analyses use 367 sufficiently complete responses (recommended_include=True).",
        "The Q15 theme chart uses all 341 nonblank hope-to-gain responses.",
        "Predictor models use two predictors at a time and describe associations, not causal effects.",
    ],
    "limitations": [
        "Q10–Q13 numeric anchors are absent from the export and should be confirmed.",
        "OLS models treat ordinal outcomes as approximately numeric; robust intervals reduce but do not eliminate that limitation.",
        "Q3 and Q6 contain structural missingness from survey versions and branching.",
        "Q21 contains unmapped numeric class codes, so class-level comparisons are omitted.",
        "Waves mix different courses and sample sizes, so year patterns are not causal trends.",
        "Q15 coding requires human review; a second reviewer should check a sample before formal reporting.",
    ],
}

FIGURES: dict[int, FigureContent] = {
    1: {
        "id": 1,
        "title": "Figure 1. Overall response patterns",
        "image": "ordinal_distributions.png",
        "summary": (
            "This figure summarizes five survey questions regarding the topics "
            "listed on the y-axis. Bars extending toward the right represent more "
            "positive or more frequent responses."
        ),
        "bullets": [
            "Workforce readiness: Most students entered the course feeling at least somewhat ready for the workforce; 76% selected one of the top two readiness categories.",
            "Coursework preparedness: Positive, with about 83% in the top two categories.",
            "Excitement about the CUBEs project: High before the project began; about 83% were somewhat or very excited.",
            "Networking: Lower-rated area. Most respondents selected seldom or sometimes.",
        ],
        "note": (
            "These questions had different wording, and networking has four choices "
            "rather than five. The bars depict patterns within each item rather than "
            "across the topics for comparison."
        ),
        "note_kind": "warning",
    },
    2: {
        "id": 2,
        "title": "Figure 2. Pre-survey skill profile: Combined whisker plot",
        "image": "skill_profile.png",
        "summary": (
            "This figure compares student ratings on current proficiency, perceived "
            "career benefit, and expected improvement for nine skills prior to "
            "beginning the course project."
        ),
        "bullets": [
            "Teamwork had the highest current-proficiency rating (4.26 out of 5) and the highest career-benefit rating (4.36).",
            "Data analysis and public speaking had relatively low current-proficiency ratings (3.01 and 3.14) but considerably higher career-benefit and expected-improvement ratings. These gaps point to skills students considered valuable areas for growth.",
            "Students expected the most improvement in research (3.94), data analysis (3.83), teamwork (3.76), and critical thinking (3.75).",
            "Career-benefit ratings were high across all nine skills, even where students rated their current proficiency lower.",
        ],
        "note": (
            "The export contains numeric values but not the written anchors for "
            "Q10–Q12. Use the means mainly for relative comparisons until the "
            "scale anchors are confirmed."
        ),
        "note_kind": "info",
    },
    3: {
        "id": 3,
        "title": "Figure 3. Relationships among pre-survey measures",
        "image": "construct_correlation_heatmap.png",
        "summary": (
            "This heatmap shows the correlation between corresponding pairs of "
            "survey measures, or how strongly they move together. The statistic "
            "shown is Spearman’s rho, ranging from −1 to 1; larger positive values "
            "mean higher ratings tend to occur together."
        ),
        "bullets": [
            "Looking forward to the project and CUBEs excitement have the strongest relationship (rho = 0.66). These two items capture project enthusiasm among students.",
            "Current proficiency, career benefit, and expected improvement seem to have moderately positive connections, with correlations from 0.46 to 0.54.",
            "Qualifications vs. job market has a clear relationship with workforce readiness (0.44).",
            "Workforce readiness and CUBEs excitement are almost unrelated (0.04), showing that general career confidence and project enthusiasm are distinct overall.",
        ],
        "note": (
            "Correlations do not capture cause and effect. Interpret the patterns "
            "as observed tendency rather than definitive outcomes."
        ),
        "note_kind": "warning",
    },
    4: {
        "id": 4,
        "title": "Figure 4. Predictors of workforce readiness",
        "image": "predictors_workforce_readiness.png",
        "summary": (
            "This figure shows average workforce readiness rating across "
            "qualification levels. The lines each represent low, middle, and high "
            "current-proficiency groups."
        ),
        "bullets": [
            "Workforce readiness generally rises as students give higher ratings on their qualifications compared to the job market.",
            "Across many qualification levels, students in the higher-proficiency group also report higher readiness.",
            "Higher career confidence and proficiency report higher readiness.",
            "The two-predictor model explains about 23% of readiness differences. Qualifications has the stronger adjusted relationship (standardized beta 0.37), while current proficiency adds a smaller independent relationship (beta 0.23).",
        ],
        "note": (
            "The lower rating categories in workforce readiness have slightly wider "
            "confidence intervals. Cells with fewer than five students are omitted, "
            "and the lines should not be interpreted as causal trends."
        ),
        "note_kind": "warning",
    },
    5: {
        "id": 5,
        "title": "Figure 5. Predictors of coursework preparedness",
        "image": "predictors_coursework_preparedness.png",
        "summary": (
            "This figure shows average coursework preparedness across "
            "workforce-readiness levels, with separate lines for "
            "current-proficiency groups."
        ),
        "bullets": [
            "Students who felt more ready for the workforce generally also felt more prepared for their coursework.",
            "Current proficiency adds a smaller relationship after readiness is considered.",
            "Together, readiness and proficiency explain about 12% of preparedness differences. The standardized coefficients are 0.28 for readiness and 0.14 for proficiency (small positive relation).",
        ],
        "note": (
            "The lower rating categories in workforce readiness have small samples "
            "and wide confidence intervals. Cells with fewer than five students are "
            "omitted, and the lines should not be interpreted as causal trends."
        ),
        "note_kind": "warning",
    },
    6: {
        "id": 6,
        "title": "Figure 6. Predictors of CUBEs excitement",
        "image": "predictors_cubes_excitement.png",
        "summary": (
            "This figure shows average CUBEs excitement across ratings of how much "
            "students looked forward to the project. Lines represent low, middle, "
            "and high expected-improvement groups."
        ),
        "bullets": [
            "Excitement rises sharply as the looking-forward rating increases.",
            "At the highest looking-forward levels, excitement is high in all expected-improvement groups, and the three lines are fairly close.",
            "The model explains about 46% of excitement differences. Looking forward is a dominant predictor (standardized beta 0.65).",
            "Expected improvement is small after looking forward is included (beta 0.07, with an interval that crosses zero).",
        ],
        "note": (
            "Looking forward and excitement are conceptually similar, so this strong "
            "relationship should not be treated as a surprising or determining "
            "factor. Small cells are omitted."
        ),
        "note_kind": "warning",
    },
    7: {
        "id": 7,
        "title": "Figure 7. Relative strength of the simple predictors",
        "image": "predictor_standardized_coefficients.png",
        "summary": (
            "This coefficient plot places all six predictors on the same "
            "standardized scale. Points farther right have stronger positive "
            "adjusted relationships with their outcome."
        ),
        "bullets": [
            "Looking forward to the project is the strongest predictor shown (beta 0.65) for CUBEs excitement.",
            "Qualifications vs. job market is the strongest workforce readiness predictor (beta 0.37), followed by current proficiency (0.23).",
            "Workforce readiness is more strongly related to coursework preparedness (0.28) than current proficiency is (0.14).",
            "Expected improvement has little independent relationship with excitement after looking-forward is included (0.07).",
        ],
        "note": (
            "Each outcome has only two predictors. The intervals use robust standard "
            "errors, but the ordinal outcomes are treated as approximately numeric "
            "and the results remain descriptive."
        ),
        "note_kind": "info",
    },
    8: {
        "id": 8,
        "title": "Figure 8. Prior activities and expected career contribution",
        "image": "q5_selection_q6_contribution.png",
        "summary": (
            "The left panel shows prior course activities that students took part "
            "in. The right panel shows student ratings on career contribution of "
            "corresponding prior activities."
        ),
        "bullets": [
            "Research projects were the most common prior activity (71%), followed by case studies (54%), business plans (39%), and real-organization projects (20%).",
            "Business plans had the highest average contribution rating (2.63 out of 4). Research projects averaged 2.30, real-organization projects 2.12, and case studies 1.89.",
            "The Q6 sample is much smaller than the Q5 sample: matched counts range from 17 to 46.",
        ],
        "note": (
            "Q6 was absent before 2025 and follows survey branching. Its results "
            "describe a small, recent subset and should not be generalized to the "
            "full pre-survey sample."
        ),
        "note_kind": "warning",
    },
    9: {
        "id": 9,
        "title": "Figure 9. Patterns across survey years",
        "image": "wave_trends.png",
        "summary": (
            "These three panels show a timeseries plot of how average workforce "
            "readiness, coursework preparedness, and CUBEs project excitement "
            "ratings change from 2022 through 2026."
        ),
        "bullets": [
            "Workforce readiness and coursework preparedness fluctuate within a fairly narrow range; neither shows a consistent upward or downward pattern.",
            "CUBEs excitement is highest in 2026 (3.53), after also being relatively high in 2024. Overall, there has been growth in excitement rating over the years analyzed.",
            "The 2026 group has only 34 students, compared with 137 in 2025 and 98 in 2022.",
        ],
        "note": (
            "Different courses and students participated each year. These lines are "
            "descriptive wave comparisons, not evidence that the survey outcomes "
            "changed because of time."
        ),
        "note_kind": "warning",
    },
    10: {
        "id": 10,
        "title": "Figure 10. Themes in what students hoped to gain",
        "image": "q15_theme_frequency.png",
        "summary": (
            "This bar chart summarizes themes in 341 open-ended answers to "
            "“What do you hope to gain from this course?” Each response could "
            "receive more than one theme."
        ),
        "bullets": [
            "Knowledge or conceptual understanding was the most common theme, appearing in 183 responses (53.7%).",
            "Business, marketing, or management appeared in 140 responses (41.1%).",
            "Applied or real-world experience appeared in 75 responses (22.0%), and research, data, or analytics appeared in 73 (21.4%).",
            "Career readiness appeared in 46 responses (13.5%), while smaller groups mentioned community impact, problem-solving, confidence, communication, teaching, and teamwork.",
        ],
        "note": (
            "Themes were assigned with keyword-assisted, multi-label rules and "
            "required human review. Percentages exceed 100% in total. Original "
            "open-ended text is not shown in this app."
        ),
        "note_kind": "info",
    },
    11: {
        "id": 11,
        "title": "Figure 11. Missing data and survey structure",
        "image": "missingness_quality.png",
        "summary": (
            "This figure shows the percentage of rows missing in each key variable "
            "column. Orange indicates missingness mainly caused by survey versions "
            "or branching."
        ),
        "bullets": [
            "Q6 items are missing from 87% to 90% of all rows because Q6 was added only in 2025 and was connected to Q5 activity choices.",
            "Q3 is missing for about 59% because it was absent before 2024 and was asked only of students who were working.",
            "Q15 and Q5 are each missing for about 24%.",
            "Most core outcomes have lower missingness, generally about 12% to 18% in the full 447-row file.",
        ],
        "note": (
            "High Q3 and Q6 missingness is expected by design. These blanks should "
            "not be replaced with zeros or treated as ordinary nonresponse."
        ),
        "note_kind": "warning",
    },
}
