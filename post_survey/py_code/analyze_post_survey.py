#!/usr/bin/env python3
"""Reproducible descriptive analysis and hybrid theme coding for the CUBEs post-survey.

The script is read-only with respect to post_survey/data_cleaned. All derived
tables, review files, figures, and documentation are written to
post_survey/analysis_output (or --outdir).
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


SKILLS = [
    "Teamwork",
    "Research",
    "Creativity",
    "Critical Thinking",
    "Professional Writing",
    "Public Speaking",
    "Leadership",
    "Data Analysis",
    "Computer/technological Skills",
]
MEASURE_LABELS = {
    "current_proficiency": "Current proficiency (Q10)",
    "career_benefit": "Career benefit (Q11)",
    "actual_improvement": "Actual improvement (Q12)",
}
Q6_MAP = {
    "Q5__project_for_a_local_international_real_b": (
        "Real business/organization project",
        "Q6_1_ord",
    ),
    "Q5__research_project": ("Research project", "Q6_2_ord"),
    "Q5__case_study_in_textbook_or_any_other_publ": ("Case study", "Q6_3_ord"),
    "Q5__business_plan_project": ("Business plan", "Q6_4_ord"),
    "Q5__other_please_specify": ("Other", "Q6_5_ord"),
}
LIKERT = {
    "Q4": (
        "Workforce readiness",
        ["Very not ready", "Somewhat not ready", "Neither ready nor not ready",
         "Somewhat ready", "Very ready"],
    ),
    "Q7": (
        "Coursework preparedness",
        ["Very unprepared", "Somewhat unprepared", "Neither prepared nor unprepared",
         "Somewhat prepared", "Very prepared"],
    ),
    "Q8": (
        "Networking frequency",
        ["Seldom (less than once per year)", "Sometimes (once per year)",
         "Frequently (once per semester)", "Often (more than 2x per semester)"],
    ),
    "Q9": (
        "Qualifications vs. job market",
        ["Very much less qualified", "Somewhat less qualified",
         "Neither more or less qualified", "Somewhat more qualified",
         "Very much more qualified"],
    ),
    "Q14": (
        "Benefit of CUBEs real-world project",
        ["Very unbeneficial", "Somewhat unbeneficial",
         "Neither beneficial nor unbeneficial", "Somewhat beneficial", "Very beneficial"],
    ),
}

# Rules intentionally favor transparency over forced agreement with exploratory counts.
# Each response can receive multiple themes; the matched phrase is retained for review.
THEME_RULES = {
    "knowledge_understanding": [
        r"\bknow(?:ledge|ing)?\b", r"\blearn(?:ed|t|ing)?\b", r"\bunderstand(?:ing)?\b",
        r"\binsight\b", r"\bperspective\b", r"\bawareness\b", r"\binformation\b",
        r"\beducat(?:ion|ed)\b", r"\bconcepts?\b",
    ],
    "business_marketing_management": [
        r"\bbusiness\b", r"\bmarketing\b", r"\bmanagement\b", r"\bmanag(?:e|ing|ement)\b",
        r"\bbranding\b", r"\bbrand\b", r"\bconsumer\b", r"\boperations?\b",
        r"\bentrepreneur", r"\bcompan(?:y|ies)\b", r"\bbusinesses\b", r"\bstrategy\b",
        r"\bstrategic\b", r"\bmarket\b", r"\bfinancial\b", r"\bfinance\b",
    ],
    "research_data_analytics": [
        r"\bresearch(?:ing|ed)?\b", r"\bdata\b", r"\banaly(?:sis|ze|zing|tics)\b", r"\bsurvey\b",
        r"\bstatistics?\b", r"\bstatistical\b", r"\bforecast", r"\bfocus group",
        r"\binterviews?\b", r"\bfindings?\b", r"\bquantitative\b", r"\bqualitative\b",
        r"\bevidence\b",
    ],
    "applied_real_world_experience": [
        r"\breal[- ]world\b", r"\breal life\b", r"\bhands[- ]on\b", r"\bclient\b",
        r"\bactual (?:business|company|organization|project)\b", r"\bpractical\b",
        r"\bapplication\b", r"\bapply\b", r"\bworked with\b",
        r"\bproject experience\b", r"\bprofessional experience\b",
    ],
    "teamwork_collaboration": [
        r"\bteam(?:work|mate|mates|s|building)?\b", r"\bcollaborat", r"\bgroup work\b",
        r"\bworking (?:in|with|as) a group\b", r"\bwork with others\b",
        r"\bwork with other people\b", r"\bcooperat", r"\bgroup dynamics?\b",
    ],
    "communication_presentation": [
        r"\bcommunicat", r"\bpresent(?:ation|ations|ing|ed)?\b", r"\bpublic speaking\b",
        r"\bspeaking\b", r"\bwriting\b", r"\bwritten\b", r"\breport(?:ing|s)?\b",
        r"\bverbal\b", r"\baudience\b", r"\bdebat(?:e|ing)\b",
    ],
    "planning_problem_solving_leadership": [
        r"\bplan(?:ning|ned)?\b", r"\bproblem[- ]solv", r"\bcritical thinking\b",
        r"\bcreativ", r"\bleadership\b", r"\blead(?:ing|er)?\b", r"\btime management\b",
        r"\borganiz(?:e|ed|ing|ation)\b", r"\brecommendations?\b", r"\bsolutions?\b",
        r"\bdecision[- ]making\b", r"\bproject management\b",
    ],
    "career_readiness": [
        r"\bcareer\b", r"\bworkforce\b", r"\bworkplace\b", r"\bjob\b", r"\bemploy",
        r"\bresume\b", r"\bprofession(?:al|ally)\b", r"\bpost[- ]graduation\b",
        r"\bfuture work\b",
    ],
    "confidence_personal_growth": [
        r"\bconfiden", r"\bpersonal growth\b", r"\bgrew\b", r"\bgrow(?:th)?\b",
        r"\bself[- ]", r"\bcomfortable\b", r"\bcomfort zone\b", r"\bproud\b",
        r"\binterest in\b", r"\bmotivated\b",
    ],
    "civic_community_social_impact": [
        r"\bcommunity\b", r"\bcivic\b", r"\bsocial work\b", r"\bsocial impact\b",
        r"\badvoc", r"\bgovernment\b", r"\bpublic policy\b", r"\bnonprofit\b",
        r"\bmental health\b", r"\bunderserved\b", r"\bsociety\b", r"\bservice\b",
        r"\bhomeless", r"\bpoli(?:tical)? science\b",
    ],
    "sustainability_environment": [
        r"\bsustainab", r"\benvironmental\b", r"\beco[- ]?friendly\b",
        r"\bclimate\b", r"\bgreen\b", r"\becological\b", r"\bcarbon\b",
    ],
    "international_intercultural": [
        r"\binternational\b", r"\bintercultural\b", r"\bcultur(?:e|al|es)\b",
        r"\bglobal\b", r"\bother countr", r"\bdifferent countr", r"\btime zones?\b",
        r"\bcoil\b", r"\bforeign\b", r"\babroad\b", r"\boverseas\b", r"\bmexico\b",
    ],
    "networking_connections": [
        r"\bnetwork(?:ing|ed)?\b", r"\bconnections?\b", r"\bcontacts?\b",
        r"\bguest speakers?\b", r"\bindustry professionals?\b",
    ],
    "technology_software": [
        r"\bsoftware\b", r"\btechnology\b", r"\btechnical\b", r"\bcomputer\b",
        r"\bexcel\b", r"\bspss\b", r"\br studio\b", r"\btableau\b", r"\bdatabase\b",
        r"\bdigital tools?\b",
    ],
    "teaching_pedagogy": [
        r"\bteach(?:er|ing)?\b", r"\blesson plans?\b", r"\bclassroom\b",
        r"\bpedagog", r"\binstructional\b", r"\bcurriculum\b",
    ],
}
THEME_LABELS = {
    "knowledge_understanding": "Knowledge / conceptual understanding",
    "business_marketing_management": "Business / marketing / management",
    "research_data_analytics": "Research / data / analytics",
    "applied_real_world_experience": "Applied / client / real-world experience",
    "teamwork_collaboration": "Teamwork / collaboration",
    "communication_presentation": "Communication / presentation",
    "planning_problem_solving_leadership": "Planning / problem-solving / leadership",
    "career_readiness": "Career readiness",
    "confidence_personal_growth": "Confidence / personal growth",
    "civic_community_social_impact": "Civic / community / social impact",
    "sustainability_environment": "Sustainability / environment",
    "international_intercultural": "International / intercultural",
    "networking_connections": "Networking / connections",
    "technology_software": "Technology / software",
    "teaching_pedagogy": "Teaching / pedagogy",
}
EXPLORATORY_COUNTS = {
    "knowledge_understanding": 126,
    "business_marketing_management": 71,
    "research_data_analytics": 62,
    "applied_real_world_experience": 60,
    "teamwork_collaboration": 41,
    "communication_presentation": 41,
    "planning_problem_solving_leadership": 33,
    "career_readiness": 21,
    "confidence_personal_growth": 20,
    "civic_community_social_impact": 20,
    "sustainability_environment": 17,
    "international_intercultural": 11,
    "networking_connections": 6,
    "technology_software": 6,
    "teaching_pedagogy": 4,
}

DIRECT_IDENTIFIERS = {
    "Q19", "student_id", "IPAddress", "ResponseId", "RecipientLastName",
    "RecipientFirstName", "RecipientEmail", "ExternalReference",
    "LocationLatitude", "LocationLongitude",
}
PALETTE = {
    "blue": "#35618F",
    "orange": "#C4772B",
    "green": "#4E7D5B",
    "red": "#A85252",
    "gray": "#7A7F87",
    "light": "#D8DEE6",
}


def read_inputs(input_dir: Path) -> dict[str, pd.DataFrame]:
    files = {
        "analysis": "03_analysis_dataset.csv",
        "dictionary": "04_data_dictionary.csv",
        "multiselect": "05_multiselect_indicators.csv",
        "multiselect_long": "05b_multiselect_long.csv",
        "skills": "06_skills_long.csv",
    }
    frames = {name: pd.read_csv(input_dir / filename) for name, filename in files.items()}
    frames["analysis"]["recommended_include"] = (
        frames["analysis"]["recommended_include"].astype(str).str.lower().eq("true")
    )
    return frames


def save_csv(df: pd.DataFrame, outdir: Path, name: str) -> None:
    df.to_csv(outdir / name, index=False, encoding="utf-8-sig")


def variable_inventory(
    analysis: pd.DataFrame, dictionary: pd.DataFrame, skills: pd.DataFrame
) -> pd.DataFrame:
    dd = dictionary.set_index("variable_code")
    rows = []
    for col in analysis.columns:
        s = analysis[col]
        if col in dd.index:
            label = dd.at[col, "display_label"]
            original = dd.at[col, "original_label"]
            vtype = dd.at[col, "variable_type"]
        else:
            label, original = col, ""
            if col.endswith("_ord"):
                vtype = "derived ordinal"
            elif col.startswith("flag_") or col in {
                "recommended_include", "any_flag", "age_implausible", "age_unparsed"
            }:
                vtype = "derived flag"
            elif pd.api.types.is_numeric_dtype(s):
                vtype = "derived numeric"
            else:
                vtype = "derived categorical"
        if col.startswith(("Q10_", "Q11_", "Q12_")):
            role = "skill rating"
        elif col.endswith("_ord") or col in {"Q13_1"}:
            role = "ordinal/rating outcome"
        elif col.startswith("Q5__"):
            role = "multi-select indicator"
        elif col.startswith("flag_") or col in {"recommended_include", "any_flag"}:
            role = "quality/control"
        elif col in {"Q15", "Q2_5_TEXT", "Q3_3_TEXT", "Q5_5_TEXT", "Q6_5_TEXT", "Q18_10_TEXT"}:
            role = "open text"
        elif col in {"wave_year", "wave_month", "Q2", "Q3", "Q17_proposed"}:
            role = "grouping variable"
        else:
            role = "supporting variable"
        direction = ""
        if col.endswith("_ord"):
            direction = "Higher = more positive/frequent"
        elif re.fullmatch(r"Q1[0-3]_\d+", col):
            direction = "Higher assumed = more of construct; anchors require confirmation"
        rows.append({
            "dataset": "03_analysis_dataset",
            "grain": "one row per respondent/wave",
            "variable": col,
            "display_label": label,
            "original_label": original,
            "variable_type": vtype,
            "analysis_role": role,
            "n_valid": int(s.notna().sum()),
            "n_missing": int(s.isna().sum()),
            "pct_missing": round(s.isna().mean() * 100, 1),
            "n_unique": int(s.nunique(dropna=True)),
            "scale_direction": direction,
        })
    rows.append({
        "dataset": "06_skills_long",
        "grain": "respondent × 9 skills × 3 measures",
        "variable": "(dataset structure)",
        "display_label": "Skills long table",
        "original_label": "",
        "variable_type": "long-format analytical table",
        "analysis_role": "skill profiles and within-skill comparisons",
        "n_valid": len(skills),
        "n_missing": int(skills["value"].isna().sum()),
        "pct_missing": round(skills["value"].isna().mean() * 100, 1),
        "n_unique": int(skills["row_id"].nunique()),
        "scale_direction": "Higher assumed = more of measure; anchors require confirmation",
    })
    return pd.DataFrame(rows)


def descriptive_statistics(analysis: pd.DataFrame) -> pd.DataFrame:
    primary = analysis.loc[analysis["recommended_include"]].copy()
    rows = []
    numeric_targets = (
        ["age", "Duration (in seconds)", "Q4_ord", "Q7_ord", "Q8_ord", "Q9_ord", "Q14_ord", "Q13_1"]
        + [f"Q{q}_{i}" for q in (10, 11, 12) for i in range(1, 10)]
    )
    categorical_targets = ["Q2", "Q3", "Q17_proposed", "wave_year", "Q4", "Q7", "Q8", "Q9", "Q14"]
    for sample_name, frame in [("recommended", primary), ("all_rows", analysis)]:
        for col in numeric_targets:
            if col not in frame:
                continue
            s = pd.to_numeric(frame[col], errors="coerce")
            rows.append({
                "sample": sample_name, "variable": col, "statistic": "numeric_summary",
                "category": "", "n": int(s.notna().sum()), "missing_n": int(s.isna().sum()),
                "missing_pct": round(s.isna().mean() * 100, 1),
                "mean": s.mean(), "sd": s.std(), "median": s.median(),
                "q1": s.quantile(.25), "q3": s.quantile(.75),
                "min": s.min(), "max": s.max(), "count": np.nan, "percent": np.nan,
            })
        for col in categorical_targets:
            if col not in frame:
                continue
            denom = frame[col].notna().sum()
            for category, count in frame[col].value_counts(dropna=False).items():
                rows.append({
                    "sample": sample_name, "variable": col, "statistic": "category_frequency",
                    "category": "(Missing)" if pd.isna(category) else str(category),
                    "n": int(denom), "missing_n": int(frame[col].isna().sum()),
                    "missing_pct": round(frame[col].isna().mean() * 100, 1),
                    "mean": np.nan, "sd": np.nan, "median": np.nan, "q1": np.nan,
                    "q3": np.nan, "min": np.nan, "max": np.nan,
                    "count": int(count), "percent": round(count / len(frame) * 100, 1),
                })
    return pd.DataFrame(rows)


def cronbach_alpha(frame: pd.DataFrame) -> tuple[float, int, float]:
    complete = frame.dropna()
    n = len(complete)
    if n < 2:
        return np.nan, n, np.nan
    k = complete.shape[1]
    item_var = complete.var(axis=0, ddof=1).sum()
    total_var = complete.sum(axis=1).var(ddof=1)
    alpha = k / (k - 1) * (1 - item_var / total_var) if total_var else np.nan
    corr = complete.corr()
    mean_interitem = corr.where(np.triu(np.ones(corr.shape), 1).astype(bool)).stack().mean()
    return alpha, n, mean_interitem


def skill_outputs(
    analysis: pd.DataFrame, skills: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ids = set(analysis.loc[analysis["recommended_include"], "row_id"])
    primary_long = skills[skills["row_id"].isin(ids)].copy()
    summary = (
        primary_long.groupby(["measure", "skill"], observed=True)["value"]
        .agg(n="count", mean="mean", sd="std", median="median")
        .reset_index()
    )
    summary["se"] = summary["sd"] / np.sqrt(summary["n"])
    summary["ci95_low"] = summary["mean"] - 1.96 * summary["se"]
    summary["ci95_high"] = summary["mean"] + 1.96 * summary["se"]
    reliability = []
    enriched = analysis.copy()
    for question, measure in [("Q10", "current_proficiency"), ("Q11", "career_benefit"),
                              ("Q12", "actual_improvement")]:
        cols = [f"{question}_{i}" for i in range(1, 10)]
        primary = analysis.loc[analysis["recommended_include"], cols]
        alpha, n_complete, mean_interitem = cronbach_alpha(primary)
        reliability.append({
            "question": question, "measure": measure, "items": len(cols),
            "n_complete": n_complete, "cronbach_alpha": alpha,
            "mean_interitem_correlation": mean_interitem,
        })
        enriched[f"{question}_mean"] = analysis[cols].mean(axis=1)
        enriched[f"{question}_n_answered"] = analysis[cols].notna().sum(axis=1)
    return summary, pd.DataFrame(reliability), enriched


def pairwise_correlations(analysis: pd.DataFrame) -> pd.DataFrame:
    primary = analysis.loc[analysis["recommended_include"]].copy()
    variables = [
        "Q4_ord", "Q7_ord", "Q8_ord", "Q9_ord", "Q10_mean", "Q11_mean",
        "Q12_mean", "Q13_1", "Q14_ord",
    ]
    rows = []
    for method in ["spearman", "pearson"]:
        for i, left in enumerate(variables):
            for right in variables[i + 1:]:
                pair = primary[[left, right]].dropna()
                rows.append({
                    "method": method, "variable_1": left, "variable_2": right,
                    "n_pairwise": len(pair),
                    "correlation": pair[left].corr(pair[right], method=method)
                    if len(pair) >= 3 else np.nan,
                })
    return pd.DataFrame(rows)


def group_wave_summary(analysis: pd.DataFrame) -> pd.DataFrame:
    primary = analysis.loc[analysis["recommended_include"]].copy()
    outcomes = ["Q4_ord", "Q7_ord", "Q8_ord", "Q9_ord", "Q10_mean",
                "Q11_mean", "Q12_mean", "Q13_1", "Q14_ord"]
    rows = []
    for group_var in ["wave_year", "Q2", "Q17_proposed"]:
        for group, sub in primary.groupby(group_var, dropna=False):
            group_n = len(sub)
            for outcome in outcomes:
                valid = pd.to_numeric(sub[outcome], errors="coerce")
                rows.append({
                    "group_variable": group_var,
                    "group": "(Missing)" if pd.isna(group) else str(group),
                    "group_n": group_n,
                    "small_group_n_lt15": group_n < 15,
                    "outcome": outcome,
                    "n_valid": int(valid.notna().sum()),
                    "mean": valid.mean(),
                    "sd": valid.std(),
                    "median": valid.median(),
                })
    return pd.DataFrame(rows)


def q5_q6_summary(analysis: pd.DataFrame) -> pd.DataFrame:
    primary = analysis.loc[analysis["recommended_include"]].copy()
    q5_answered = primary["Q5"].notna()
    denom = int(q5_answered.sum())
    rows = []
    for indicator, (activity, q6_col) in Q6_MAP.items():
        selected = primary[indicator].eq(1)
        matched = selected & primary[q6_col].notna()
        contribution = pd.to_numeric(primary.loc[matched, q6_col], errors="coerce")
        rows.append({
            "activity": activity,
            "q5_indicator": indicator,
            "q6_ordinal": q6_col,
            "q5_answered_n": denom,
            "selected_n": int(selected.sum()),
            "selected_pct_of_q5_answered": round(selected.sum() / denom * 100, 1) if denom else np.nan,
            "matched_q6_n": int(contribution.notna().sum()),
            "matched_q6_mean": contribution.mean(),
            "matched_q6_sd": contribution.std(),
            "matched_q6_median": contribution.median(),
            "q6_missing_is_skip_logic": True,
        })
    return pd.DataFrame(rows)


def matched_phrases(text: str, patterns: list[str]) -> list[str]:
    found = []
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            found.append(match.group(0))
    return sorted(set(found), key=str.lower)


def theme_code_q15(analysis: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source = analysis.loc[analysis["Q15"].notna() & analysis["Q15"].astype(str).str.strip().ne(""),
                          ["row_id", "Q15", "recommended_include", "wave_year"]].copy()
    rows = []
    negative_pattern = re.compile(
        r"\b(nothing|none|not much|didn.?t gain|did not gain|waste|stress|stressful|"
        r"confus(?:ed|ing)|disappoint|frustrat|hate|poorly|no benefit)\b", re.I
    )
    none_pattern = re.compile(
        r"\b(nothing|none|not much|didn.?t gain|did not gain|gained nothing|no meaningful gain)\b",
        re.I,
    )
    extrinsic_pattern = re.compile(r"\b(credit|grade|pass(?:ing)? the class|course requirement)\b", re.I)
    low_specificity_pattern = re.compile(
        r"^\s*(a lot|knowledge|experience|skills?|information|understanding|insight|"
        r"learned a lot|new things|many things|everything|something)\s*[.!]?\s*$", re.I
    )
    for rec in source.itertuples(index=False):
        text = str(rec.Q15).strip()
        record = {
            "row_id": rec.row_id,
            "response_text_RESTRICTED": text,
            "recommended_include": rec.recommended_include,
            "wave_year": rec.wave_year,
        }
        evidence = {}
        for theme, patterns in THEME_RULES.items():
            hits = matched_phrases(text, patterns)
            record[theme] = bool(hits)
            record[f"{theme}__evidence"] = " | ".join(hits)
            evidence[theme] = hits
        record["no_meaningful_gain"] = bool(none_pattern.search(text))
        record["extrinsic_only"] = bool(extrinsic_pattern.search(text)) and not any(
            record[t] for t in THEME_RULES
        )
        record["negative_or_critical"] = bool(negative_pattern.search(text))
        record["low_specificity"] = bool(low_specificity_pattern.search(text))
        n_themes = sum(bool(record[t]) for t in THEME_RULES)
        record["n_substantive_themes"] = n_themes
        reasons = []
        if n_themes == 0:
            reasons.append("no_theme")
        if n_themes > 5:
            reasons.append("over_coded_gt5")
        if record["negative_or_critical"]:
            reasons.append("negative_or_critical")
        if record["low_specificity"]:
            reasons.append("low_specificity")
        if record["extrinsic_only"]:
            reasons.append("extrinsic_only")
        record["manual_review"] = bool(reasons)
        record["manual_review_reason"] = ";".join(reasons)
        rows.append(record)
    assignments = pd.DataFrame(rows)
    n_nonblank = len(assignments)
    frequencies = []
    for theme in THEME_RULES:
        count = int(assignments[theme].sum())
        frequencies.append({
            "theme": theme,
            "theme_label": THEME_LABELS[theme],
            "count": count,
            "pct_nonblank_q15": round(count / n_nonblank * 100, 1),
            "denominator_nonblank_q15": n_nonblank,
            "multi_label": True,
            "exploratory_manual_count": EXPLORATORY_COUNTS[theme],
            "difference_from_exploratory": count - EXPLORATORY_COUNTS[theme],
        })
    for flag in ["no_meaningful_gain", "extrinsic_only", "negative_or_critical", "low_specificity"]:
        count = int(assignments[flag].sum())
        frequencies.append({
            "theme": flag,
            "theme_label": flag.replace("_", " ").title(),
            "count": count,
            "pct_nonblank_q15": round(count / n_nonblank * 100, 1),
            "denominator_nonblank_q15": n_nonblank,
            "multi_label": True,
            "exploratory_manual_count": np.nan,
            "difference_from_exploratory": np.nan,
        })
    codebook = pd.DataFrame([
        {
            "theme": theme,
            "theme_label": THEME_LABELS[theme],
            "definition": {
                "knowledge_understanding": "Explicit learning, knowledge, insight, awareness, or understanding.",
                "business_marketing_management": "Business, marketing, management, operations, strategy, or entrepreneurship.",
                "research_data_analytics": "Research methods, data collection/analysis, statistics, surveys, or findings.",
                "applied_real_world_experience": "Practical application, live clients, hands-on work, or real-world experience.",
                "teamwork_collaboration": "Team, group, cooperation, or collaboration skills and experience.",
                "communication_presentation": "Presentation, public speaking, writing, reporting, or communication.",
                "planning_problem_solving_leadership": "Planning, problem-solving, leadership, creativity, organization, or recommendations.",
                "career_readiness": "Career, job, workplace, resume, employment, or professional preparation.",
                "confidence_personal_growth": "Confidence, comfort, motivation, self-development, or personal growth.",
                "civic_community_social_impact": "Community, civic, advocacy, nonprofit, public service, or social impact learning.",
                "sustainability_environment": "Sustainability, climate, environmental, ecological, or green practices.",
                "international_intercultural": "International, cultural, global, country, or COIL experience.",
                "networking_connections": "Networking, professional connections, contacts, or guest speakers.",
                "technology_software": "Software, databases, computers, technical tools, or technology.",
                "teaching_pedagogy": "Teaching, classroom, lesson plans, pedagogy, students, or curriculum.",
            }[theme],
            "regex_patterns": " | ".join(THEME_RULES[theme]),
            "coding_unit": "full Q15 response",
            "assignment": "binary multi-label; manual review required for ambiguous cases",
        }
        for theme in THEME_RULES
    ])
    review = assignments.loc[assignments["manual_review"]].copy()
    return assignments, pd.DataFrame(frequencies), codebook, review


def normalize_other_text(analysis: pd.DataFrame) -> pd.DataFrame:
    specs = {
        "Q2_5_TEXT": [
            ("part_time_plus_internship", r"part.?time.*intern|intern.*part.?time"),
            ("part_time_or_occasional", r"part.?time|one day|if i am needed"),
            ("military_service", r"air national|military|guard"),
            ("graduate_assistantship", r"graduate assist"),
            ("job_seeking", r"searching|seeking"),
        ],
        "Q3_3_TEXT": [
            ("mixed_multiple_jobs", r"\bboth\b|one (?:job )?is|one isn"),
            ("adjacent_specialty", r"chosen field|law enforcement|clinical"),
            ("preparatory_role", r"preschool|teaching prep"),
            ("future_field_job", r"starting soon|will be working"),
        ],
        "Q5_5_TEXT": [
            ("none_not_applicable", r"^(no|not really|i have not|n/?a)$"),
            ("interview_writing_project", r"interview.*writing"),
            ("international_collaboration", r"coil|international"),
        ],
        "Q6_5_TEXT": [
            ("international_collaboration", r"coil|international"),
        ],
        # Instructor/course names are deliberately not copied to this output.
        "Q18_10_TEXT": [
            ("course_or_instructor_other_internal", r".+"),
        ],
    }
    rows = []
    for col, rules in specs.items():
        subset = analysis.loc[analysis[col].notna() & analysis[col].astype(str).str.strip().ne(""),
                              ["row_id", col]]
        for rec in subset.itertuples(index=False, name=None):
            row_id, raw = rec
            text = str(raw).strip()
            normalized = "manual_review"
            for category, pattern in rules:
                if re.search(pattern, text, flags=re.I):
                    normalized = category
                    break
            rows.append({
                "row_id": row_id,
                "source_variable": col,
                "normalized_category": normalized,
                "manual_review": normalized == "manual_review",
                "raw_text_included": False,
                "privacy_note": (
                    "Raw instructor/course text intentionally omitted"
                    if col == "Q18_10_TEXT" else
                    "Review original in cleaned respondent-level source if needed"
                ),
            })
    return pd.DataFrame(rows)


def chart_theme_frequency(theme_frequency: pd.DataFrame, figures: Path) -> None:
    data = theme_frequency[theme_frequency["theme"].isin(THEME_RULES)].sort_values("count")
    fig, ax = plt.subplots(figsize=(10, 7.5))
    bars = ax.barh(data["theme_label"], data["pct_nonblank_q15"], color=PALETTE["blue"])
    for bar, row in zip(bars, data.itertuples(index=False)):
        ax.text(bar.get_width() + .5, bar.get_y() + bar.get_height() / 2,
                f"{row.count} ({row.pct_nonblank_q15:.1f}%)", va="center", fontsize=8)
    ax.set_title("Themes in responses to “What did you gain from this course?”")
    ax.set_xlabel("Percentage of nonblank Q15 responses (%)")
    ax.set_ylabel("Multi-label theme")
    ax.set_xlim(0, max(data["pct_nonblank_q15"].max() * 1.23, 10))
    ax.text(0, -0.16,
            "Multiple themes may be assigned per respondent; percentages do not sum to 100%. "
            f"N={int(data['denominator_nonblank_q15'].iloc[0])} nonblank responses.\n"
            "Source: CUBEs post-project survey, 2022–2026; hybrid keyword-assisted coding, manual review required.",
            transform=ax.transAxes, fontsize=8, color="#444444")
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "q15_theme_frequency.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_likert(analysis: pd.DataFrame, figures: Path) -> None:
    primary = analysis.loc[analysis["recommended_include"]]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    colors = ["#A85252", "#D69A75", "#D8DEE6", "#82A58C", "#35618F"]
    for y, (variable, (label, levels)) in enumerate(LIKERT.items()):
        valid = primary[variable].where(~(
            (variable == "Q14") & primary["Q14_is_numeric_code"].astype(str).str.lower().eq("true")
        )).dropna()
        counts = valid.value_counts()
        n = len(valid)
        pct = np.array([counts.get(level, 0) / n * 100 if n else 0 for level in levels])
        color_idx = np.rint(np.linspace(0, 4, len(levels))).astype(int)
        if len(levels) == 5:
            left = -(pct[0] + pct[1] + pct[2] / 2)
        else:
            left = -pct[:len(levels) // 2].sum()
        for value, idx in zip(pct, color_idx):
            ax.barh(y, value, left=left, color=colors[idx], height=.66)
            left += value
        ax.text(101, y, f"n={n}", va="center", fontsize=8)
    labels = [LIKERT[v][0] for v in LIKERT]
    ax.set_yticks(range(len(labels)), labels)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=color, label=legend)
        for color, legend in zip(
            colors, ["Lowest", "Low", "Midpoint (5-level items)", "High", "Highest"]
        )
    ]
    ax.set_title("Post-survey ordinal response distributions")
    ax.set_xlabel("Respondents within item (%) — lower responses left, higher responses right")
    ax.set_ylabel("Survey construct")
    ax.set_xlim(-108, 108)
    ticks = np.arange(-100, 101, 20)
    ax.set_xticks(ticks, [str(abs(t)) for t in ticks])
    ax.axvline(0, color="#555555", linewidth=.8)
    ax.legend(handles=handles, title="Relative response order", bbox_to_anchor=(1.01, 1),
              loc="upper left",
              fontsize=7, title_fontsize=8)
    ax.text(0, -0.17,
            "Primary sample: recommended_include=True. Q14 unlabeled numeric code 41 excluded. "
            "Q8 has four categories.\nSource: CUBEs post-project survey, 2022–2026.",
            transform=ax.transAxes, fontsize=8, color="#444444")
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "ordinal_distributions.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_skill_profile(skill_summary: pd.DataFrame, figures: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 7))
    offsets = {"current_proficiency": -.18, "career_benefit": 0, "actual_improvement": .18}
    colors = {"current_proficiency": PALETTE["blue"], "career_benefit": PALETTE["orange"],
              "actual_improvement": PALETTE["green"]}
    ybase = np.arange(len(SKILLS))
    for measure in MEASURE_LABELS:
        sub = skill_summary[skill_summary["measure"] == measure].set_index("skill").reindex(SKILLS)
        y = ybase + offsets[measure]
        ax.errorbar(sub["mean"], y,
                    xerr=[sub["mean"] - sub["ci95_low"], sub["ci95_high"] - sub["mean"]],
                    fmt="o", capsize=2, color=colors[measure], label=MEASURE_LABELS[measure])
    ax.set_yticks(ybase, SKILLS)
    ax.invert_yaxis()
    ax.set_xlim(0, 5.25)
    ax.set_xlabel("Mean rating (0–5 numeric export)")
    ax.set_ylabel("Skill")
    ax.set_title("Skill proficiency, career benefit, and reported improvement")
    ax.legend(loc="lower right")
    ax.text(0, -0.14,
            "Points are means; error bars are approximate 95% confidence intervals. "
            "Numeric anchors require confirmation.\nPrimary sample: recommended_include=True. "
            "Source: CUBEs post-project survey, 2022–2026.",
            transform=ax.transAxes, fontsize=8, color="#444444")
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "skill_profile.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_correlation(correlations: pd.DataFrame, figures: Path) -> None:
    data = correlations[correlations["method"] == "spearman"]
    variables = ["Q4_ord", "Q7_ord", "Q8_ord", "Q9_ord", "Q10_mean",
                 "Q11_mean", "Q12_mean", "Q13_1", "Q14_ord"]
    labels = ["Readiness", "Preparedness", "Networking", "Qualifications",
              "Proficiency", "Career benefit", "Improvement", "Enjoyment", "CUBEs benefit"]
    matrix = pd.DataFrame(np.eye(len(variables)), index=variables, columns=variables)
    for rec in data.itertuples(index=False):
        matrix.loc[rec.variable_1, rec.variable_2] = rec.correlation
        matrix.loc[rec.variable_2, rec.variable_1] = rec.correlation
    matrix.index = labels
    matrix.columns = labels
    fig, ax = plt.subplots(figsize=(10, 9.5))
    sns.heatmap(matrix, vmin=-1, vmax=1, center=0, cmap="vlag", annot=True, fmt=".2f",
                square=True, linewidths=.5, cbar_kws={"label": "Spearman correlation"}, ax=ax)
    ax.set_title("Relationships among post-survey constructs")
    ax.set_xlabel("Survey construct")
    ax.set_ylabel("Survey construct")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    fig.subplots_adjust(left=.17, right=.93, top=.9, bottom=.27)
    fig.text(.17, .035,
             "Pairwise-complete Spearman correlations; association does not imply causation.\n"
             "Primary sample: recommended_include=True. Source: CUBEs post-project survey, 2022–2026.",
             fontsize=8, color="#444444")
    fig.savefig(figures / "construct_correlation_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_enjoyment_benefit(analysis: pd.DataFrame, figures: Path) -> None:
    primary = analysis.loc[analysis["recommended_include"] & analysis["Q14_ord"].notna()]
    table = pd.crosstab(primary["Q14_ord"], primary["Q13_1"]).reindex(
        index=range(5), columns=range(6), fill_value=0
    )
    fig, ax = plt.subplots(figsize=(8.5, 5.8))
    sns.heatmap(table, annot=True, fmt="d", cmap="Blues", ax=ax,
                cbar_kws={"label": "Respondent count"})
    ax.set_title("Project enjoyment by perceived CUBEs benefit")
    ax.set_xlabel("Project enjoyment rating (Q13, 0–5)")
    ax.set_ylabel("CUBEs benefit ordinal code (Q14, 0–4)")
    ax.text(0, -0.18,
            f"N={int(table.to_numpy().sum())} pairwise-complete respondents; Q14 code 41 excluded.\n"
            "Primary sample: recommended_include=True. Source: CUBEs post-project survey, 2022–2026.",
            transform=ax.transAxes, fontsize=8, color="#444444")
    fig.tight_layout()
    fig.savefig(figures / "enjoyment_by_benefit_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_q5_q6(summary: pd.DataFrame, figures: Path) -> None:
    data = summary[summary["activity"] != "Other"].sort_values(
        "selected_pct_of_q5_answered", ascending=True
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.7), sharey=True)
    axes[0].barh(data["activity"], data["selected_pct_of_q5_answered"], color=PALETTE["blue"])
    axes[0].set_xlabel("Selected among Q5 respondents (%)")
    axes[0].set_ylabel("Prior activity")
    axes[0].set_title("Q5 activity selection")
    for y, value in enumerate(data["selected_pct_of_q5_answered"]):
        axes[0].text(value + 1, y, f"{value:.1f}%", va="center", fontsize=8)
    axes[1].barh(data["activity"], data["matched_q6_mean"], color=PALETTE["orange"])
    axes[1].set_xlim(0, 4.4)
    axes[1].set_xlabel("Mean matched contribution rating (0–4)")
    axes[1].set_title("Q6 contribution among matched selectors")
    for y, rec in enumerate(data.itertuples(index=False)):
        axes[1].text(rec.matched_q6_mean + .05, y,
                     f"{rec.matched_q6_mean:.2f} (n={rec.matched_q6_n})",
                     va="center", fontsize=8)
    fig.suptitle("Prior course activities and perceived career contribution", y=1.02)
    fig.text(.01, -.02,
             "Q6 missingness follows Q5 skip logic; contribution means are conditional on selection and "
             "response, not causal effects.\nPrimary sample: recommended_include=True. "
             "Source: CUBEs post-project survey, 2022–2026.", fontsize=8, color="#444444")
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "q5_selection_q6_contribution.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_wave_trends(group_summary: pd.DataFrame, figures: Path) -> None:
    labels = {
        "Q4_ord": "Workforce readiness", "Q7_ord": "Course preparedness",
        "Q8_ord": "Networking frequency", "Q10_mean": "Mean proficiency",
        "Q12_mean": "Mean improvement", "Q14_ord": "CUBEs benefit",
    }
    data = group_summary[
        (group_summary["group_variable"] == "wave_year")
        & group_summary["outcome"].isin(labels)
    ].copy()
    data["year"] = pd.to_numeric(data["group"])
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.5), sharex=True)
    for ax, (outcome, title) in zip(axes.flat, labels.items()):
        sub = data[data["outcome"] == outcome].sort_values("year")
        ax.plot(sub["year"], sub["mean"], marker="o", color=PALETTE["blue"])
        for rec in sub.itertuples(index=False):
            ax.annotate(f"n={rec.n_valid}", (rec.year, rec.mean), xytext=(0, 7),
                        textcoords="offset points", ha="center", fontsize=7)
        ax.set_title(title)
        ax.set_ylabel("Mean rating")
        ax.set_xlabel("Survey year")
        ax.set_xticks(sorted(sub["year"].unique()))
        ax.grid(axis="y", alpha=.2)
    fig.suptitle("Post-survey construct means by survey year", y=1.01)
    fig.text(.01, -.01,
             "Descriptive trends only; 2026 is a smaller sample and Dec 2025 wave assignment requires review.\n"
             "Primary sample: recommended_include=True. Source: CUBEs post-project survey, 2022–2026.",
             fontsize=8, color="#444444")
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "wave_trends.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_missingness(analysis: pd.DataFrame, figures: Path) -> None:
    targets = ["Q3", "Q5", "Q6_1", "Q6_2", "Q6_3", "Q6_4", "Q7", "Q8", "Q9",
               "Q10_1", "Q11_1", "Q12_1", "Q13_1", "Q14", "Q15", "Q18", "age"]
    structural = {"Q3", "Q6_1", "Q6_2", "Q6_3", "Q6_4"}
    data = pd.DataFrame({
        "variable": targets,
        "missing_pct": [analysis[c].isna().mean() * 100 for c in targets],
        "missingness_type": ["Structural/skip logic" if c in structural else "Item nonresponse / eligibility"
                             for c in targets],
    }).sort_values("missing_pct")
    fig, ax = plt.subplots(figsize=(9.5, 6.8))
    colors = data["missingness_type"].map({
        "Structural/skip logic": PALETTE["orange"],
        "Item nonresponse / eligibility": PALETTE["blue"],
    })
    ax.barh(data["variable"], data["missing_pct"], color=colors)
    for y, value in enumerate(data["missing_pct"]):
        ax.text(value + .7, y, f"{value:.1f}%", va="center", fontsize=8)
    handles = [
        plt.Line2D([0], [0], color=PALETTE["orange"], lw=8, label="Structural/skip logic"),
        plt.Line2D([0], [0], color=PALETTE["blue"], lw=8, label="Item nonresponse / eligibility"),
    ]
    ax.legend(handles=handles, loc="lower right")
    ax.set_title("Missingness in key post-survey variables")
    ax.set_xlabel("Missing respondent rows (%)")
    ax.set_ylabel("Variable")
    ax.set_xlim(0, max(data["missing_pct"].max() * 1.15, 10))
    ax.text(0, -0.13,
            "All 345 rows. Structural labels reflect survey version/branching documented in the cleaning report.\n"
            "Source: CUBEs post-project survey, 2022–2026.",
            transform=ax.transAxes, fontsize=8, color="#444444")
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "missingness_quality.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def validations(
    frames: dict[str, pd.DataFrame],
    enriched: pd.DataFrame,
    assignments: pd.DataFrame,
    output_dir: Path,
) -> pd.DataFrame:
    analysis = frames["analysis"]
    skills = frames["skills"]
    dd = frames["dictionary"]
    checks = []

    def add(name: str, passed: bool, observed: object, expected: object, detail: str = "") -> None:
        checks.append({
            "check": name, "passed": bool(passed), "observed": observed,
            "expected": expected, "detail": detail,
        })

    add("analysis row count", len(analysis) == 345, len(analysis), 345)
    add("analysis row_id unique", analysis["row_id"].is_unique, analysis["row_id"].nunique(), 345)
    add("skills long row count", len(skills) == 9315, len(skills), 9315)
    rows_per_id = skills.groupby("row_id").size()
    add("27 skill rows per respondent", rows_per_id.eq(27).all(),
        f"{rows_per_id.min()}–{rows_per_id.max()}", 27)
    add("recommended sample count", analysis["recommended_include"].sum() == 280,
        int(analysis["recommended_include"].sum()), 280)
    q14_codes = analysis["Q14_is_numeric_code"].astype(str).str.lower().eq("true")
    add("Q14 code 41 excluded from ordinal", analysis.loc[q14_codes, "Q14_ord"].isna().all(),
        int(analysis.loc[q14_codes, "Q14_ord"].notna().sum()), 0)
    q6_labels = dd.set_index("variable_code")["display_label"]
    add("Q6_1 post meaning", "Real-organization" in str(q6_labels.get("Q6_1", "")),
        q6_labels.get("Q6_1", ""), "Real-organization project")
    add("Q6_2 post meaning", "Research" in str(q6_labels.get("Q6_2", "")),
        q6_labels.get("Q6_2", ""), "Research project")
    q5_missing = analysis["Q5"].isna()
    q5_indicators = [c for c in analysis if c.startswith("Q5__") and c not in {
        "Q5__n_selected", "Q5__other_text"
    }]
    add("Q5 unanswered remains missing", analysis.loc[q5_missing, q5_indicators].isna().all().all(),
        int(analysis.loc[q5_missing, q5_indicators].notna().sum().sum()), 0)
    exposed = sorted(DIRECT_IDENTIFIERS.intersection(analysis.columns))
    add("analysis excludes direct identifiers", not exposed, ", ".join(exposed), "none")
    add("Q15 nonblank count", len(assignments) == 237, len(assignments), 237)
    add("theme assignments unique by row", assignments["row_id"].is_unique,
        assignments["row_id"].nunique(), len(assignments))
    figures = list((output_dir / "figures").glob("*.png"))
    add("expected figure count", len(figures) == 8, len(figures), 8)
    results = pd.DataFrame(checks)
    if not results["passed"].all():
        failed = results.loc[~results["passed"], "check"].tolist()
        raise AssertionError(f"Validation failed: {failed}")
    return results


def make_readme(
    outdir: Path,
    analysis: pd.DataFrame,
    reliability: pd.DataFrame,
    correlations: pd.DataFrame,
    theme_frequency: pd.DataFrame,
    review: pd.DataFrame,
) -> None:
    primary_n = int(analysis["recommended_include"].sum())
    spearman = correlations[correlations["method"] == "spearman"].copy()

    def corr(a: str, b: str) -> float:
        match = spearman[
            ((spearman["variable_1"] == a) & (spearman["variable_2"] == b))
            | ((spearman["variable_1"] == b) & (spearman["variable_2"] == a))
        ]
        return float(match.iloc[0]["correlation"]) if len(match) else np.nan

    top_themes = theme_frequency[theme_frequency["theme"].isin(THEME_RULES)].nlargest(4, "count")
    theme_lines = "\n".join(
        f"- {r.theme_label}: {int(r.count)} ({r.pct_nonblank_q15:.1f}%)"
        for r in top_themes.itertuples(index=False)
    )
    alpha_lines = "\n".join(
        f"- {r.question} {MEASURE_LABELS[r.measure]}: α={r.cronbach_alpha:.3f} "
        f"(complete n={int(r.n_complete)})"
        for r in reliability.itertuples(index=False)
    )
    text = f"""# CUBEs Post-Survey Analysis Output

Generated by `post_survey/py_code/analyze_post_survey.py`.

## Scope and denominators

- Respondent rows: {len(analysis)}
- Primary quantitative sample (`recommended_include=True`): {primary_n}
- Q15 nonblank responses: {int(theme_frequency['denominator_nonblank_q15'].max())}
- Survey years: 2022–2026
- Quantitative findings are descriptive associations, not causal effects.

## Principal findings

- Project enjoyment and perceived CUBEs benefit move together (Spearman ρ={corr('Q13_1', 'Q14_ord'):.2f}).
- Workforce readiness and perceived job-market qualifications are related (ρ={corr('Q4_ord', 'Q9_ord'):.2f}).
- Mean proficiency and career benefit form the strongest skill-block relationship (ρ={corr('Q10_mean', 'Q11_mean'):.2f}).
- Q6 contribution summaries are conditional on Q5 selection and survey branching; missing Q6 is primarily skip logic.

Scale reliability:
{alpha_lines}

Most frequent hybrid-coded Q15 themes:
{theme_lines}

## Q15 coding method

Q15 uses transparent keyword/phrase-assisted, multi-label coding. A response may receive multiple
themes, so percentages do not sum to 100%. The assignment file retains matched evidence and is
marked restricted because it contains original free text. Broad, unmatched, negative, extrinsic,
and over-coded responses are routed to `q15_manual_review_RESTRICTED.csv`.

This is an exploratory single-coder framework. Manually review and revise the codebook, then
double-code a sample and report agreement before treating theme prevalence as definitive.
Current manual-review queue: {len(review)} responses.

## Output files

- `variable_inventory.csv`: dataset structure, types, roles, labels, and missingness.
- `descriptive_statistics.csv`: recommended-sample and all-row summaries.
- `skill_summary.csv`, `scale_reliability.csv`, `respondent_block_means.csv`.
- `correlations.csv`: Spearman primary and Pearson sensitivity correlations with pairwise n.
- `group_and_wave_summary.csv`: wave, work-status, and gender summaries; small groups flagged.
- `q5_q6_activity_summary.csv`: activity selection and matched contribution ratings.
- `q15_theme_codebook.csv`, `q15_theme_frequency.csv`.
- `q15_theme_assignments_RESTRICTED.csv`: original Q15 text, themes, and matched evidence.
- `q15_manual_review_RESTRICTED.csv`: assignments requiring human review.
- `other_text_normalization.csv`: normalized sparse “Other” categories; instructor names omitted.
- `validation_results.csv`: row-count, scale, skip-logic, and privacy checks.
- `figures/`: eight high-resolution PNG charts.

## Important limitations

- Q10–Q13 numeric anchors are absent from the export and need confirmation.
- Q14 has seven unlabeled code-41 responses; they are excluded from ordinal calculations.
- Q18 contains 126 unmapped numeric class codes; class-level comparisons are not produced.
- Q8 wording differs from the pre-survey, and Q12–Q14 measure post-specific constructs.
- Q3 and Q6 have structural missingness. Do not treat it as random item nonresponse.
- Repeated student IDs require a defined matching/deduplication rule for longitudinal analyses.
- Wave and subgroup summaries are descriptive; groups with n<15 are flagged.
"""
    (outdir / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    script_dir = Path(__file__).resolve().parent
    post_dir = script_dir.parent
    parser.add_argument("--input-dir", type=Path, default=post_dir / "data_cleaned")
    parser.add_argument("--outdir", type=Path, default=post_dir / "analysis_output")
    args = parser.parse_args()

    outdir = args.outdir.resolve()
    figures = outdir / "figures"
    outdir.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    frames = read_inputs(args.input_dir.resolve())
    analysis = frames["analysis"]

    inventory = variable_inventory(analysis, frames["dictionary"], frames["skills"])
    descriptive = descriptive_statistics(analysis)
    skill_summary, reliability, enriched = skill_outputs(analysis, frames["skills"])
    correlations = pairwise_correlations(enriched)
    groups = group_wave_summary(enriched)
    q5q6 = q5_q6_summary(enriched)

    save_csv(inventory, outdir, "variable_inventory.csv")
    save_csv(descriptive, outdir, "descriptive_statistics.csv")
    save_csv(skill_summary, outdir, "skill_summary.csv")
    save_csv(reliability, outdir, "scale_reliability.csv")
    save_csv(
        enriched[["row_id", "recommended_include", "Q10_mean", "Q10_n_answered",
                  "Q11_mean", "Q11_n_answered", "Q12_mean", "Q12_n_answered"]],
        outdir, "respondent_block_means.csv",
    )
    save_csv(correlations, outdir, "correlations.csv")
    save_csv(groups, outdir, "group_and_wave_summary.csv")
    save_csv(q5q6, outdir, "q5_q6_activity_summary.csv")

    assignments, theme_frequency, codebook, review = theme_code_q15(analysis)
    save_csv(codebook, outdir, "q15_theme_codebook.csv")
    save_csv(theme_frequency, outdir, "q15_theme_frequency.csv")
    save_csv(assignments, outdir, "q15_theme_assignments_RESTRICTED.csv")
    save_csv(review, outdir, "q15_manual_review_RESTRICTED.csv")
    save_csv(normalize_other_text(analysis), outdir, "other_text_normalization.csv")

    chart_theme_frequency(theme_frequency, figures)
    chart_likert(analysis, figures)
    chart_skill_profile(skill_summary, figures)
    chart_correlation(correlations, figures)
    chart_enjoyment_benefit(enriched, figures)
    chart_q5_q6(q5q6, figures)
    chart_wave_trends(groups, figures)
    chart_missingness(analysis, figures)

    validation = validations(frames, enriched, assignments, outdir)
    save_csv(validation, outdir, "validation_results.csv")
    make_readme(outdir, enriched, reliability, correlations, theme_frequency, review)

    print(f"Analysis complete: {outdir}")
    print(f"Respondents: {len(analysis)}; recommended sample: {int(analysis['recommended_include'].sum())}")
    print(f"Q15 nonblank: {len(assignments)}; manual review: {len(review)}")
    print("Theme count differences from exploratory manual estimates:")
    print(theme_frequency.loc[
        theme_frequency["theme"].isin(THEME_RULES),
        ["theme", "count", "exploratory_manual_count", "difference_from_exploratory"],
    ].to_string(index=False))
    print(f"Validation checks passed: {int(validation['passed'].sum())}/{len(validation)}")


if __name__ == "__main__":
    main()
