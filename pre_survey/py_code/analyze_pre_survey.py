#!/usr/bin/env python3
"""Reproducible descriptive and simple predictor analysis for the CUBEs pre-survey.

Cleaned inputs are read-only. All derived tables, figures, restricted theme
assignments, and documentation are written to pre_survey/analysis_output.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent.parent
SHARED_PATH = WORKSPACE / "post_survey" / "py_code" / "analyze_post_survey.py"
spec = importlib.util.spec_from_file_location("post_analysis_shared", SHARED_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load shared analysis helpers from {SHARED_PATH}")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)

SKILLS = shared.SKILLS
THEME_RULES = shared.THEME_RULES
THEME_LABELS = shared.THEME_LABELS
DIRECT_IDENTIFIERS = (shared.DIRECT_IDENTIFIERS | {"Q22"}) - {"pseudo_id", "Q19"}
PALETTE = shared.PALETTE

MEASURE_LABELS = {
    "current_proficiency": "Current proficiency (Q10)",
    "career_benefit": "Career benefit (Q11)",
    "expected_improvement": "Expected improvement (Q12)",
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
         "Frequently (once per semester)", "Often (more than 2x per year)"],
    ),
    "Q9": (
        "Qualifications vs. job market",
        ["Very much less qualified", "Somewhat less qualified",
         "Neither more or less qualified", "Somewhat more qualified",
         "Very much more qualified"],
    ),
    "Q14": (
        "Excitement about CUBEs project",
        ["Very unexcited", "Somewhat unexcited", "Neither excited nor unexcited",
         "Somewhat excited", "Very excited"],
    ),
}
Q5_Q6_MAP = {
    "Q5__research_project": ("Research project", "Q6_1_ord"),
    "Q5__project_for_a_local_international_real_o": (
        "Real-organization project", "Q6_2_ord"
    ),
    "Q5__case_study_in_textbook_or_any_other_publ": ("Case study", "Q6_3_ord"),
    "Q5__business_plan_project": ("Business plan", "Q6_4_ord"),
}
MODEL_SPECS = (
    {
        "model": "Workforce readiness",
        "outcome": "Q4_ord",
        "outcome_label": "Workforce readiness",
        "predictors": ("Q9_ord", "Q10_mean"),
        "predictor_labels": ("Qualifications vs. job market", "Current proficiency"),
    },
    {
        "model": "Coursework preparedness",
        "outcome": "Q7_ord",
        "outcome_label": "Coursework preparedness",
        "predictors": ("Q4_ord", "Q10_mean"),
        "predictor_labels": ("Workforce readiness", "Current proficiency"),
    },
    {
        "model": "CUBEs excitement",
        "outcome": "Q14_ord",
        "outcome_label": "CUBEs excitement",
        "predictors": ("Q13_1", "Q12_mean"),
        "predictor_labels": ("Looking forward to project", "Expected skill improvement"),
    },
)
THEME_DEFINITIONS = {
    "knowledge_understanding": "Learning, knowledge, insight, awareness, or conceptual understanding.",
    "business_marketing_management": "Business, marketing, management, strategy, operations, or entrepreneurship.",
    "research_data_analytics": "Research, data collection/analysis, statistics, surveys, or evidence.",
    "applied_real_world_experience": "Practical, client-based, hands-on, or real-world experience.",
    "teamwork_collaboration": "Team, group, cooperation, or collaboration skills.",
    "communication_presentation": "Communication, presentation, public speaking, writing, or reporting.",
    "planning_problem_solving_leadership": "Planning, problem-solving, leadership, creativity, or project organization.",
    "career_readiness": "Career, job, workplace, resume, or professional preparation.",
    "confidence_personal_growth": "Confidence, comfort, self-development, motivation, or personal growth.",
    "civic_community_social_impact": "Community, civic, advocacy, nonprofit, public-service, or social-impact learning.",
    "sustainability_environment": "Sustainability, environmental, ecological, climate, or green practices.",
    "international_intercultural": "International, intercultural, global, country, or COIL experience.",
    "networking_connections": "Networking, professional connections, contacts, or guest speakers.",
    "technology_software": "Technology, software, databases, computers, or technical tools.",
    "teaching_pedagogy": "Teaching, classrooms, lesson plans, pedagogy, or curriculum.",
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


def save_csv(frame: pd.DataFrame, outdir: Path, filename: str) -> None:
    frame.to_csv(outdir / filename, index=False, encoding="utf-8-sig")


def skill_outputs(
    analysis: pd.DataFrame, skills: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    primary_ids = set(analysis.loc[analysis["recommended_include"], "row_id"])
    primary_long = skills[skills["row_id"].isin(primary_ids)].copy()
    summary = (
        primary_long.groupby(["measure", "skill"], observed=True)["value"]
        .agg(n="count", mean="mean", sd="std", median="median")
        .reset_index()
    )
    summary["se"] = summary["sd"] / np.sqrt(summary["n"])
    summary["ci95_low"] = summary["mean"] - 1.96 * summary["se"]
    summary["ci95_high"] = summary["mean"] + 1.96 * summary["se"]

    enriched = analysis.copy()
    reliability = []
    for question, measure in [
        ("Q10", "current_proficiency"),
        ("Q11", "career_benefit"),
        ("Q12", "expected_improvement"),
    ]:
        columns = [f"{question}_{i}" for i in range(1, 10)]
        block = analysis.loc[analysis["recommended_include"], columns]
        alpha, n_complete, mean_interitem = shared.cronbach_alpha(block)
        reliability.append({
            "question": question,
            "measure": measure,
            "items": len(columns),
            "n_complete": n_complete,
            "cronbach_alpha": alpha,
            "mean_interitem_correlation": mean_interitem,
        })
        enriched[f"{question}_mean"] = analysis[columns].mean(axis=1)
        enriched[f"{question}_n_answered"] = analysis[columns].notna().sum(axis=1)
    enriched["Q13_mean"] = pd.to_numeric(enriched["Q13_1"], errors="coerce")
    return summary, pd.DataFrame(reliability), enriched


def descriptive_statistics(analysis: pd.DataFrame) -> pd.DataFrame:
    return shared.descriptive_statistics(analysis)


def pairwise_correlations(analysis: pd.DataFrame) -> pd.DataFrame:
    primary = analysis.loc[analysis["recommended_include"]]
    variables = [
        "Q4_ord", "Q7_ord", "Q8_ord", "Q9_ord", "Q10_mean",
        "Q11_mean", "Q12_mean", "Q13_1", "Q14_ord",
    ]
    rows = []
    for method in ("spearman", "pearson"):
        for index, left in enumerate(variables):
            for right in variables[index + 1:]:
                pair = primary[[left, right]].dropna()
                rows.append({
                    "method": method,
                    "variable_1": left,
                    "variable_2": right,
                    "n_pairwise": len(pair),
                    "correlation": (
                        pair[left].corr(pair[right], method=method)
                        if len(pair) >= 3 else np.nan
                    ),
                })
    return pd.DataFrame(rows)


def group_wave_summary(analysis: pd.DataFrame) -> pd.DataFrame:
    return shared.group_wave_summary(analysis)


def q5_q6_summary(analysis: pd.DataFrame) -> pd.DataFrame:
    primary = analysis.loc[analysis["recommended_include"]].copy()
    q5_answered = primary["Q5"].notna()
    denominator = int(q5_answered.sum())
    rows = []
    for indicator, (activity, q6_column) in Q5_Q6_MAP.items():
        selected = primary[indicator].eq(1)
        matched = selected & primary[q6_column].notna()
        contribution = pd.to_numeric(primary.loc[matched, q6_column], errors="coerce")
        rows.append({
            "activity": activity,
            "q5_indicator": indicator,
            "q6_ordinal": q6_column,
            "q5_answered_n": denominator,
            "selected_n": int(selected.sum()),
            "selected_pct_of_q5_answered": (
                round(selected.sum() / denominator * 100, 1) if denominator else np.nan
            ),
            "matched_q6_n": int(contribution.notna().sum()),
            "matched_q6_mean": contribution.mean(),
            "matched_q6_sd": contribution.std(),
            "matched_q6_median": contribution.median(),
            "q6_missing_is_structural_or_skip_logic": True,
        })
    return pd.DataFrame(rows)


def model_outputs(
    analysis: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    primary = analysis.loc[analysis["recommended_include"]].copy()
    rows = []
    diagnostics = []
    for model_spec in MODEL_SPECS:
        outcome = model_spec["outcome"]
        predictors = list(model_spec["predictors"])
        columns = [outcome] + predictors
        data = primary[columns].apply(pd.to_numeric, errors="coerce").dropna()
        y = data[outcome]
        x = sm.add_constant(data[predictors], has_constant="add")
        fit = sm.OLS(y, x).fit(cov_type="HC3")

        z = data.copy()
        z = (z - z.mean()) / z.std(ddof=0)
        fit_z = sm.OLS(z[outcome], sm.add_constant(z[predictors], has_constant="add")).fit(
            cov_type="HC3"
        )
        influence = fit.get_influence()
        cooks = influence.cooks_distance[0]
        ceiling_pct = (y >= 3).mean() * 100
        diagnostics.append({
            "model": model_spec["model"],
            "outcome": outcome,
            "n": len(data),
            "r_squared": fit.rsquared,
            "adjusted_r_squared": fit.rsquared_adj,
            "outcome_ceiling_pct_categories_3_or_4": ceiling_pct,
            "cooks_d_gt_4_over_n": int((cooks > 4 / len(data)).sum()),
            "max_cooks_d": float(np.max(cooks)),
            "robust_covariance": "HC3",
            "design": "cross-sectional descriptive association",
        })
        predictor_label_map = dict(zip(predictors, model_spec["predictor_labels"]))
        conf = fit.conf_int()
        conf_z = fit_z.conf_int()
        for term in ["const"] + predictors:
            rows.append({
                "model": model_spec["model"],
                "outcome": outcome,
                "outcome_label": model_spec["outcome_label"],
                "n": len(data),
                "r_squared": fit.rsquared,
                "adjusted_r_squared": fit.rsquared_adj,
                "term": term,
                "term_label": "Intercept" if term == "const" else predictor_label_map[term],
                "coefficient": fit.params[term],
                "robust_se_hc3": fit.bse[term],
                "ci95_low": conf.loc[term, 0],
                "ci95_high": conf.loc[term, 1],
                "p_value": fit.pvalues[term],
                "standardized_beta": (
                    np.nan if term == "const" else fit_z.params[term]
                ),
                "standardized_ci95_low": (
                    np.nan if term == "const" else conf_z.loc[term, 0]
                ),
                "standardized_ci95_high": (
                    np.nan if term == "const" else conf_z.loc[term, 1]
                ),
                "standardized_p_value": (
                    np.nan if term == "const" else fit_z.pvalues[term]
                ),
            })
    return pd.DataFrame(rows), pd.DataFrame(diagnostics)


def theme_code_q15(
    analysis: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source = analysis.loc[
        analysis["Q15"].notna() & analysis["Q15"].astype(str).str.strip().ne(""),
        ["row_id", "Q15", "recommended_include", "wave_year"],
    ].copy()
    low_specificity_pattern = re.compile(
        r"^\s*(a lot|knowledge|experience|skills?|information|understanding|insight|"
        r"learned a lot|new things|many things|everything|something)\s*[.!]?\s*$",
        re.I,
    )
    negative_pattern = re.compile(
        r"\b(nothing|none|not sure|don.?t know|do not know|n/?a|no idea)\b", re.I
    )
    rows = []
    for record in source.itertuples(index=False):
        text = str(record.Q15).strip()
        coded = {
            "row_id": record.row_id,
            "response_text_RESTRICTED": text,
            "recommended_include": record.recommended_include,
            "wave_year": record.wave_year,
        }
        for theme, patterns in THEME_RULES.items():
            hits = shared.matched_phrases(text, patterns)
            coded[theme] = bool(hits)
            coded[f"{theme}__evidence"] = " | ".join(hits)
        coded["negative_or_unclear"] = bool(negative_pattern.search(text))
        coded["low_specificity"] = bool(low_specificity_pattern.search(text))
        coded["n_substantive_themes"] = sum(bool(coded[theme]) for theme in THEME_RULES)
        reasons = []
        if coded["n_substantive_themes"] == 0:
            reasons.append("no_theme")
        if coded["n_substantive_themes"] > 5:
            reasons.append("over_coded_gt5")
        if coded["negative_or_unclear"]:
            reasons.append("negative_or_unclear")
        if coded["low_specificity"]:
            reasons.append("low_specificity")
        coded["manual_review"] = bool(reasons)
        coded["manual_review_reason"] = ";".join(reasons)
        rows.append(coded)
    assignments = pd.DataFrame(rows)
    denominator = len(assignments)
    frequencies = []
    for theme in THEME_RULES:
        count = int(assignments[theme].sum())
        frequencies.append({
            "theme": theme,
            "theme_label": THEME_LABELS[theme],
            "count": count,
            "pct_nonblank_q15": round(count / denominator * 100, 1),
            "denominator_nonblank_q15": denominator,
            "multi_label": True,
        })
    for flag in ("negative_or_unclear", "low_specificity"):
        count = int(assignments[flag].sum())
        frequencies.append({
            "theme": flag,
            "theme_label": flag.replace("_", " ").title(),
            "count": count,
            "pct_nonblank_q15": round(count / denominator * 100, 1),
            "denominator_nonblank_q15": denominator,
            "multi_label": True,
        })
    codebook = pd.DataFrame([
        {
            "theme": theme,
            "theme_label": THEME_LABELS[theme],
            "definition": THEME_DEFINITIONS[theme],
            "regex_patterns": " | ".join(THEME_RULES[theme]),
            "coding_unit": "full Q15 response",
            "assignment": "binary multi-label; keyword-assisted; manual review required",
        }
        for theme in THEME_RULES
    ])
    review = assignments.loc[assignments["manual_review"]].copy()
    return assignments, pd.DataFrame(frequencies), codebook, review


def chart_ordinal_distributions(analysis: pd.DataFrame, figures: Path) -> None:
    primary = analysis.loc[analysis["recommended_include"]]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    colors = ["#A85252", "#D69A75", "#D8DEE6", "#82A58C", "#35618F"]
    for y, (variable, (label, levels)) in enumerate(LIKERT.items()):
        valid = primary[variable].dropna()
        counts = valid.value_counts()
        n = len(valid)
        pct = np.array([counts.get(level, 0) / n * 100 if n else 0 for level in levels])
        color_idx = np.rint(np.linspace(0, 4, len(levels))).astype(int)
        left = (
            -(pct[0] + pct[1] + pct[2] / 2)
            if len(levels) == 5 else -pct[:len(levels) // 2].sum()
        )
        for value, index in zip(pct, color_idx):
            ax.barh(y, value, left=left, color=colors[index], height=.66)
            left += value
        ax.text(101, y, f"n={n}", va="center", fontsize=8)
    labels = [LIKERT[variable][0] for variable in LIKERT]
    ax.set_yticks(range(len(labels)), labels)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=color, label=legend)
        for color, legend in zip(
            colors, ["Lowest", "Low", "Midpoint (5-level items)", "High", "Highest"]
        )
    ]
    ax.axvline(0, color="#555555", linewidth=.8)
    ax.set_xlim(-108, 108)
    ticks = np.arange(-100, 101, 20)
    ax.set_xticks(ticks, [str(abs(tick)) for tick in ticks])
    ax.set_title("Pre-survey ordinal response distributions")
    ax.set_xlabel("Respondents within item (%) — lower responses left, higher responses right")
    ax.set_ylabel("Survey construct")
    ax.legend(handles=handles, title="Relative response order", bbox_to_anchor=(1.01, 1),
              loc="upper left", fontsize=7, title_fontsize=8)
    ax.text(
        0, -.17,
        "Primary sample: recommended_include=True. Q8 has four categories.\n"
        "Source: CUBEs pre-project survey, 2022–2026.",
        transform=ax.transAxes, fontsize=8, color="#444444",
    )
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "ordinal_distributions.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_skill_profile(skill_summary: pd.DataFrame, figures: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 7))
    offsets = {"current_proficiency": -.18, "career_benefit": 0, "expected_improvement": .18}
    colors = {
        "current_proficiency": PALETTE["blue"],
        "career_benefit": PALETTE["orange"],
        "expected_improvement": PALETTE["green"],
    }
    ybase = np.arange(len(SKILLS))
    for measure in MEASURE_LABELS:
        subset = (
            skill_summary[skill_summary["measure"] == measure]
            .set_index("skill").reindex(SKILLS)
        )
        y = ybase + offsets[measure]
        ax.errorbar(
            subset["mean"], y,
            xerr=[
                subset["mean"] - subset["ci95_low"],
                subset["ci95_high"] - subset["mean"],
            ],
            fmt="o", capsize=2, color=colors[measure], label=MEASURE_LABELS[measure],
        )
    ax.set_yticks(ybase, SKILLS)
    ax.invert_yaxis()
    ax.set_xlim(0, 5.25)
    ax.set_xlabel("Mean rating (0–5 numeric export)")
    ax.set_ylabel("Skill")
    ax.set_title("Pre-survey skill proficiency, career benefit, and expected improvement")
    ax.legend(loc="lower right")
    ax.text(
        0, -.14,
        "Points are means; error bars are approximate 95% confidence intervals. "
        "Numeric anchors require confirmation.\nPrimary sample: recommended_include=True. "
        "Source: CUBEs pre-project survey, 2022–2026.",
        transform=ax.transAxes, fontsize=8, color="#444444",
    )
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "skill_profile.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_correlation(correlations: pd.DataFrame, figures: Path) -> None:
    data = correlations[correlations["method"] == "spearman"]
    variables = [
        "Q4_ord", "Q7_ord", "Q8_ord", "Q9_ord", "Q10_mean",
        "Q11_mean", "Q12_mean", "Q13_1", "Q14_ord",
    ]
    labels = [
        "Readiness", "Preparedness", "Networking", "Qualifications", "Proficiency",
        "Career benefit", "Expected improvement", "Looking forward", "CUBEs excitement",
    ]
    matrix = pd.DataFrame(np.eye(len(variables)), index=variables, columns=variables)
    for row in data.itertuples(index=False):
        matrix.loc[row.variable_1, row.variable_2] = row.correlation
        matrix.loc[row.variable_2, row.variable_1] = row.correlation
    matrix.index = labels
    matrix.columns = labels
    fig, ax = plt.subplots(figsize=(10, 9.5))
    sns.heatmap(
        matrix, vmin=-1, vmax=1, center=0, cmap="vlag", annot=True, fmt=".2f",
        square=True, linewidths=.5, cbar_kws={"label": "Spearman correlation"}, ax=ax,
    )
    ax.set_title("Relationships among pre-survey constructs")
    ax.set_xlabel("Survey construct")
    ax.set_ylabel("Survey construct")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    fig.subplots_adjust(left=.17, right=.93, top=.9, bottom=.27)
    fig.text(
        .17, .035,
        "Pairwise-complete Spearman correlations; association does not imply causation.\n"
        "Primary sample: recommended_include=True. Source: CUBEs pre-project survey, 2022–2026.",
        fontsize=8, color="#444444",
    )
    fig.savefig(figures / "construct_correlation_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def add_tertile(
    frame: pd.DataFrame, column: str, output: str,
    labels: tuple[str, str, str] = ("Low", "Middle", "High"),
) -> pd.DataFrame:
    result = frame.copy()
    ranked = result[column].rank(method="first")
    result[output] = pd.qcut(ranked, 3, labels=labels)
    return result


def aggregated_predictor_plot(
    analysis: pd.DataFrame,
    outcome: str,
    xvar: str,
    stratifier: str,
    strata_column: str,
    title: str,
    xlabel: str,
    ylabel: str,
    output: Path,
) -> None:
    primary = analysis.loc[analysis["recommended_include"], [outcome, xvar, stratifier]].dropna()
    primary = add_tertile(primary, stratifier, strata_column)
    grouped = (
        primary.groupby([xvar, strata_column], observed=True)[outcome]
        .agg(n="count", mean="mean", sd="std").reset_index()
    )
    grouped = grouped[grouped["n"] >= 5].copy()
    grouped["se"] = grouped["sd"] / np.sqrt(grouped["n"])
    grouped["low"] = grouped["mean"] - 1.96 * grouped["se"]
    grouped["high"] = grouped["mean"] + 1.96 * grouped["se"]
    colors = {"Low": PALETTE["gray"], "Middle": PALETTE["orange"], "High": PALETTE["blue"]}
    fig, ax = plt.subplots(figsize=(9.5, 6))
    for group in ("Low", "Middle", "High"):
        subset = grouped[grouped[strata_column] == group].sort_values(xvar)
        ax.errorbar(
            subset[xvar], subset["mean"],
            yerr=[subset["mean"] - subset["low"], subset["high"] - subset["mean"]],
            marker="o", capsize=3, linewidth=1.5, color=colors[group],
            label=f"{group} {stratifier.replace('_mean', '').replace('_', ' ')}",
        )
        for row in subset.itertuples(index=False):
            ax.annotate(
                f"n={row.n}", (getattr(row, xvar), row.mean),
                xytext=(0, 7), textcoords="offset points", ha="center", fontsize=7,
            )
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(-.1, 4.35)
    ax.set_xticks(sorted(primary[xvar].unique()))
    ax.legend(title="Predictor group")
    ax.text(
        0, -.17,
        "Points are group means; error bars are approximate 95% confidence intervals. "
        "Groups are descriptive tertiles; cells with n<5 are omitted.\n"
        "Primary sample: recommended_include=True. "
        "Source: CUBEs pre-project survey, 2022–2026.",
        transform=ax.transAxes, fontsize=8, color="#444444",
    )
    sns.despine()
    fig.tight_layout()
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_predictor_relationships(analysis: pd.DataFrame, figures: Path) -> None:
    aggregated_predictor_plot(
        analysis, "Q4_ord", "Q9_ord", "Q10_mean", "Q10_group",
        "Workforce readiness by qualifications and proficiency",
        "Qualifications compared with job market (Q9 ordinal code)",
        "Mean workforce readiness (Q4, 0–4)",
        figures / "predictors_workforce_readiness.png",
    )
    aggregated_predictor_plot(
        analysis, "Q7_ord", "Q4_ord", "Q10_mean", "Q10_group",
        "Coursework preparedness by readiness and proficiency",
        "Workforce readiness (Q4 ordinal code)",
        "Mean coursework preparedness (Q7, 0–4)",
        figures / "predictors_coursework_preparedness.png",
    )
    aggregated_predictor_plot(
        analysis, "Q14_ord", "Q13_1", "Q12_mean", "Q12_group",
        "CUBEs excitement by looking-forward and expected-improvement ratings",
        "Looking forward to project (Q13 numeric code)",
        "Mean CUBEs excitement (Q14, 0–4)",
        figures / "predictors_cubes_excitement.png",
    )


def chart_model_coefficients(model_summary: pd.DataFrame, figures: Path) -> None:
    data = model_summary[model_summary["term"] != "const"].copy()
    data["label"] = data["model"] + ": " + data["term_label"]
    data = data.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(len(data))
    colors = data["model"].map({
        "Workforce readiness": PALETTE["blue"],
        "Coursework preparedness": PALETTE["orange"],
        "CUBEs excitement": PALETTE["green"],
    })
    for index, row in data.iterrows():
        color = colors.iloc[index]
        ax.errorbar(
            row["standardized_beta"], index,
            xerr=[[
                row["standardized_beta"] - row["standardized_ci95_low"],
            ], [
                row["standardized_ci95_high"] - row["standardized_beta"],
            ]],
            fmt="o", color=color, ecolor=color, capsize=3, linewidth=2,
            markersize=6, zorder=3,
        )
    ax.set_yticks(y, data["label"])
    ax.axvline(0, color="#555555", linewidth=.8)
    ax.set_xlabel("Standardized coefficient (beta)")
    ax.set_ylabel("Outcome and predictor")
    ax.set_title("Relative strength of predictors in three simple models")
    for index, row in data.iterrows():
        ax.text(row["standardized_ci95_high"] + .02, index, f"β={row['standardized_beta']:.2f}",
                va="center", fontsize=8)
    ax.text(
        0, -.18,
        "Each outcome has two predictors; intervals use HC3 robust standard errors. "
        "Coefficients show association, not causation.\nPrimary sample: recommended_include=True. "
        "Source: CUBEs pre-project survey, 2022–2026.",
        transform=ax.transAxes, fontsize=8, color="#444444",
    )
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "predictor_standardized_coefficients.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_q5_q6(summary: pd.DataFrame, figures: Path) -> None:
    data = summary.sort_values("selected_pct_of_q5_answered", ascending=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8), sharey=True)
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
    for y, row in enumerate(data.itertuples(index=False)):
        label = (
            f"{row.matched_q6_mean:.2f} (n={row.matched_q6_n})"
            if pd.notna(row.matched_q6_mean) else "No matched responses"
        )
        value = row.matched_q6_mean if pd.notna(row.matched_q6_mean) else 0
        axes[1].text(value + .05, y, label, va="center", fontsize=8)
    fig.suptitle("Prior course activities and perceived career contribution", y=1.02)
    fig.text(
        .01, -.02,
        "Q6 was absent before 2025 and follows Q5 branching; matched Q6 samples are small. "
        "Contribution means are descriptive.\nPrimary sample: recommended_include=True. "
        "Source: CUBEs pre-project survey, 2022–2026.",
        fontsize=8, color="#444444",
    )
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "q5_selection_q6_contribution.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_wave_trends(groups: pd.DataFrame, figures: Path) -> None:
    labels = {
        "Q4_ord": "Workforce readiness",
        "Q7_ord": "Coursework preparedness",
        "Q14_ord": "CUBEs excitement",
    }
    data = groups[
        (groups["group_variable"] == "wave_year")
        & groups["outcome"].isin(labels)
    ].copy()
    data["year"] = pd.to_numeric(data["group"])
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8), sharex=True)
    for ax, (outcome, title) in zip(axes, labels.items()):
        subset = data[data["outcome"] == outcome].sort_values("year")
        ax.plot(subset["year"], subset["mean"], marker="o", color=PALETTE["blue"])
        for row in subset.itertuples(index=False):
            ax.annotate(
                f"n={row.n_valid}", (row.year, row.mean), xytext=(0, 7),
                textcoords="offset points", ha="center", fontsize=7,
            )
        ax.set_title(title)
        ax.set_ylabel("Mean ordinal rating")
        ax.set_xlabel("Survey year")
        ax.set_xticks(sorted(subset["year"].unique()))
        ax.grid(axis="y", alpha=.2)
    fig.suptitle("Pre-survey outcome means by survey year", y=1.03)
    fig.text(
        .01, -.03,
        "Descriptive trends only; wave sizes and participating courses differ.\n"
        "Primary sample: recommended_include=True. Source: CUBEs pre-project survey, 2022–2026.",
        fontsize=8, color="#444444",
    )
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "wave_trends.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_theme_frequency(theme_frequency: pd.DataFrame, figures: Path) -> None:
    data = theme_frequency[theme_frequency["theme"].isin(THEME_RULES)].sort_values("count")
    fig, ax = plt.subplots(figsize=(10, 7.5))
    bars = ax.barh(data["theme_label"], data["pct_nonblank_q15"], color=PALETTE["blue"])
    for bar, row in zip(bars, data.itertuples(index=False)):
        ax.text(
            bar.get_width() + .5, bar.get_y() + bar.get_height() / 2,
            f"{row.count} ({row.pct_nonblank_q15:.1f}%)", va="center", fontsize=8,
        )
    ax.set_title("Themes in responses to “What do you hope to gain from this course?”")
    ax.set_xlabel("Percentage of nonblank Q15 responses (%)")
    ax.set_ylabel("Multi-label theme")
    ax.set_xlim(0, max(data["pct_nonblank_q15"].max() * 1.25, 10))
    ax.text(
        0, -.16,
        "Multiple themes may be assigned per respondent; percentages do not sum to 100%. "
        f"N={int(data['denominator_nonblank_q15'].iloc[0])} nonblank responses.\n"
        "Source: CUBEs pre-project survey, 2022–2026; hybrid keyword-assisted coding, "
        "manual review required.",
        transform=ax.transAxes, fontsize=8, color="#444444",
    )
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "q15_theme_frequency.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def chart_missingness(analysis: pd.DataFrame, figures: Path) -> None:
    targets = [
        "Q3", "Q5", "Q6_1", "Q6_2", "Q6_3", "Q6_4", "Q7", "Q8", "Q9",
        "Q10_1", "Q11_1", "Q12_1", "Q13_1", "Q14", "Q15", "Q18", "age",
    ]
    structural = {"Q3", "Q6_1", "Q6_2", "Q6_3", "Q6_4"}
    data = pd.DataFrame({
        "variable": targets,
        "missing_pct": [analysis[column].isna().mean() * 100 for column in targets],
        "missingness_type": [
            "Structural/skip logic" if column in structural
            else "Item nonresponse / eligibility"
            for column in targets
        ],
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
        plt.Line2D([0], [0], color=PALETTE["blue"], lw=8,
                   label="Item nonresponse / eligibility"),
    ]
    ax.legend(handles=handles, loc="lower right")
    ax.set_title("Missingness in key pre-survey variables")
    ax.set_xlabel("Missing respondent rows (%)")
    ax.set_ylabel("Variable")
    ax.set_xlim(0, max(data["missing_pct"].max() * 1.12, 10))
    ax.text(
        0, -.13,
        "All 447 rows. Q3 and Q6 structural labels reflect survey versions and branching.\n"
        "Source: CUBEs pre-project survey, 2022–2026.",
        transform=ax.transAxes, fontsize=8, color="#444444",
    )
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "missingness_quality.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_readme(
    outdir: Path,
    analysis: pd.DataFrame,
    reliability: pd.DataFrame,
    correlations: pd.DataFrame,
    model_summary: pd.DataFrame,
    theme_frequency: pd.DataFrame,
    review: pd.DataFrame,
) -> None:
    spearman = correlations[correlations["method"] == "spearman"]

    def correlation(left: str, right: str) -> float:
        match = spearman[
            ((spearman["variable_1"] == left) & (spearman["variable_2"] == right))
            | ((spearman["variable_1"] == right) & (spearman["variable_2"] == left))
        ]
        return float(match.iloc[0]["correlation"]) if len(match) else np.nan

    top_themes = (
        theme_frequency[theme_frequency["theme"].isin(THEME_RULES)]
        .nlargest(4, "count")
    )
    theme_lines = "\n".join(
        f"- {row.theme_label}: {int(row.count)} ({row.pct_nonblank_q15:.1f}%)"
        for row in top_themes.itertuples(index=False)
    )
    reliability_lines = "\n".join(
        f"- {row.question} {MEASURE_LABELS[row.measure]}: α={row.cronbach_alpha:.3f} "
        f"(complete n={int(row.n_complete)})"
        for row in reliability.itertuples(index=False)
    )
    model_lines = []
    for model in model_summary["model"].unique():
        subset = model_summary[(model_summary["model"] == model) & (model_summary["term"] != "const")]
        predictors = "; ".join(
            f"{row.term_label} β={row.standardized_beta:.2f}"
            for row in subset.itertuples(index=False)
        )
        model_lines.append(
            f"- {model}: n={int(subset.iloc[0]['n'])}, R²={subset.iloc[0]['r_squared']:.3f}; "
            f"{predictors}."
        )
    text = f"""# CUBEs Pre-Survey Analysis Output

Generated by `pre_survey/py_code/analyze_pre_survey.py`.

## Scope and denominators

- Respondent rows: {len(analysis)}
- Primary quantitative sample (`recommended_include=True`): {int(analysis['recommended_include'].sum())}
- Q15 nonblank responses: {int(theme_frequency['denominator_nonblank_q15'].max())}
- Survey years: 2022–2026
- Results are descriptive, cross-sectional associations—not causal effects.

## Principal relationships

- Qualifications vs. the job market and workforce readiness: Spearman ρ={correlation('Q9_ord', 'Q4_ord'):.2f}.
- Current proficiency and workforce readiness: ρ={correlation('Q10_mean', 'Q4_ord'):.2f}.
- Workforce readiness and coursework preparedness: ρ={correlation('Q4_ord', 'Q7_ord'):.2f}.
- Looking forward to the project and CUBEs excitement: ρ={correlation('Q13_1', 'Q14_ord'):.2f}.

Simple two-predictor models:
{chr(10).join(model_lines)}

Scale reliability:
{reliability_lines}

Most frequent hybrid-coded Q15 hope-to-gain themes:
{theme_lines}

## Q15 coding method

Q15 uses transparent keyword/phrase-assisted, multi-label coding. A response may receive
multiple themes, so percentages do not sum to 100%. Original text and matched evidence are
restricted. Unmatched, broad, unclear, and over-coded responses are routed to
`q15_manual_review_RESTRICTED.csv`. Current review queue: {len(review)} responses.

This is an exploratory single-coder framework. Revise the codebook through manual review and
double-code a sample before treating theme prevalence as definitive.

## Key outputs

- `variable_inventory.csv`, `descriptive_statistics.csv`, and `group_and_wave_summary.csv`.
- `skill_summary.csv`, `scale_reliability.csv`, and `respondent_block_means.csv`.
- `correlations.csv`, `predictor_model_summary.csv`, and `predictor_model_diagnostics.csv`.
- `q5_q6_activity_summary.csv`.
- `q15_theme_codebook.csv` and `q15_theme_frequency.csv`.
- `q15_theme_assignments_RESTRICTED.csv` and `q15_manual_review_RESTRICTED.csv`.
- `validation_results.csv`.
- `figures/`: eleven high-resolution PNG charts.

## Important limitations

- Q10–Q13 numeric anchors are absent from the export and require confirmation.
- Q3 was absent before 2024 and is conditional on work status.
- Q6 was absent before February 2025 and follows Q5 branching; matched samples are small.
- Q21 has 151 unmapped numeric class codes in the full file, so class comparisons are omitted.
- Outcomes are concentrated in positive categories, and robust OLS still treats ordinal codes
  as approximately numeric.
- Waves contain different courses and sample sizes; wave patterns are descriptive.
- Repeated student IDs require a matching/deduplication rule for longitudinal analysis.
"""
    (outdir / "README.md").write_text(text, encoding="utf-8")


def validations(
    frames: dict[str, pd.DataFrame],
    assignments: pd.DataFrame,
    model_summary: pd.DataFrame,
    outdir: Path,
) -> pd.DataFrame:
    analysis = frames["analysis"]
    skills = frames["skills"]
    dictionary = frames["dictionary"].set_index("variable_code")
    checks = []

    def add(name: str, passed: bool, observed: object, expected: object) -> None:
        checks.append({
            "check": name, "passed": bool(passed), "observed": observed, "expected": expected,
        })

    add("analysis row count", len(analysis) == 447, len(analysis), 447)
    add("analysis row_id unique", analysis["row_id"].is_unique, analysis["row_id"].nunique(), 447)
    add("skills long row count", len(skills) == 12069, len(skills), 12069)
    rows_per_id = skills.groupby("row_id").size()
    add("27 skill rows per respondent", rows_per_id.eq(27).all(),
        f"{rows_per_id.min()}–{rows_per_id.max()}", 27)
    add("recommended sample count", analysis["recommended_include"].sum() == 367,
        int(analysis["recommended_include"].sum()), 367)
    add("Q6_1 pre meaning", "Research project" in str(dictionary.at["Q6_1", "display_label"]),
        dictionary.at["Q6_1", "display_label"], "Research project")
    add("Q6_2 pre meaning", "Real-organization" in str(dictionary.at["Q6_2", "display_label"]),
        dictionary.at["Q6_2", "display_label"], "Real-organization project")
    q5_missing = analysis["Q5"].isna()
    q5_indicators = [
        column for column in analysis
        if column.startswith("Q5__") and column not in {"Q5__n_selected", "Q5__other_text"}
    ]
    add("Q5 unanswered remains missing", analysis.loc[q5_missing, q5_indicators].isna().all().all(),
        int(analysis.loc[q5_missing, q5_indicators].notna().sum().sum()), 0)
    add("Q3 structural flag present", "q3_not_in_version" in analysis.columns,
        "q3_not_in_version" in analysis.columns, True)
    add("Q6 structural flag present", "q6_not_in_version" in analysis.columns,
        "q6_not_in_version" in analysis.columns, True)
    exposed = sorted(DIRECT_IDENTIFIERS.intersection(analysis.columns))
    add("analysis excludes direct identifiers", not exposed, ", ".join(exposed), "none")
    add("theme assignments unique", assignments["row_id"].is_unique,
        assignments["row_id"].nunique(), len(assignments))
    non_intercept = model_summary[model_summary["term"] != "const"]
    observed_n = dict(non_intercept.groupby("model")["n"].first())
    add("readiness model n", 360 <= observed_n.get("Workforce readiness", 0) <= 367,
        observed_n.get("Workforce readiness"), "approximately 366")
    add("preparedness model n", 360 <= observed_n.get("Coursework preparedness", 0) <= 367,
        observed_n.get("Coursework preparedness"), "approximately 364")
    add("excitement model n", 360 <= observed_n.get("CUBEs excitement", 0) <= 367,
        observed_n.get("CUBEs excitement"), "approximately 367")
    expected_signs = non_intercept["standardized_beta"].gt(0).all()
    add("all prespecified predictor directions positive", expected_signs,
        non_intercept["standardized_beta"].round(3).tolist(), "all positive")
    figures = list((outdir / "figures").glob("*.png"))
    add("expected figure count", len(figures) == 11, len(figures), 11)
    result = pd.DataFrame(checks)
    if not result["passed"].all():
        failed = result.loc[~result["passed"], "check"].tolist()
        raise AssertionError(f"Validation failed: {failed}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    pre_dir = SCRIPT_DIR.parent
    parser.add_argument("--input-dir", type=Path, default=pre_dir / "data_cleaned")
    parser.add_argument("--outdir", type=Path, default=pre_dir / "analysis_output")
    args = parser.parse_args()

    outdir = args.outdir.resolve()
    figures = outdir / "figures"
    outdir.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    frames = read_inputs(args.input_dir.resolve())
    analysis = frames["analysis"]
    inventory = shared.variable_inventory(analysis, frames["dictionary"], frames["skills"])
    descriptive = descriptive_statistics(analysis)
    skill_summary, reliability, enriched = skill_outputs(analysis, frames["skills"])
    correlations = pairwise_correlations(enriched)
    groups = group_wave_summary(enriched)
    q5q6 = q5_q6_summary(enriched)
    model_summary, model_diagnostics = model_outputs(enriched)
    assignments, theme_frequency, codebook, review = theme_code_q15(enriched)

    save_csv(inventory, outdir, "variable_inventory.csv")
    save_csv(descriptive, outdir, "descriptive_statistics.csv")
    save_csv(skill_summary, outdir, "skill_summary.csv")
    save_csv(reliability, outdir, "scale_reliability.csv")
    save_csv(
        enriched[
            ["row_id", "recommended_include", "Q10_mean", "Q10_n_answered",
             "Q11_mean", "Q11_n_answered", "Q12_mean", "Q12_n_answered", "Q13_mean"]
        ],
        outdir, "respondent_block_means.csv",
    )
    save_csv(correlations, outdir, "correlations.csv")
    save_csv(groups, outdir, "group_and_wave_summary.csv")
    save_csv(q5q6, outdir, "q5_q6_activity_summary.csv")
    save_csv(model_summary, outdir, "predictor_model_summary.csv")
    save_csv(model_diagnostics, outdir, "predictor_model_diagnostics.csv")
    save_csv(codebook, outdir, "q15_theme_codebook.csv")
    save_csv(theme_frequency, outdir, "q15_theme_frequency.csv")
    save_csv(assignments, outdir, "q15_theme_assignments_RESTRICTED.csv")
    save_csv(review, outdir, "q15_manual_review_RESTRICTED.csv")

    chart_ordinal_distributions(enriched, figures)
    chart_skill_profile(skill_summary, figures)
    chart_correlation(correlations, figures)
    chart_predictor_relationships(enriched, figures)
    chart_model_coefficients(model_summary, figures)
    chart_q5_q6(q5q6, figures)
    chart_wave_trends(groups, figures)
    chart_theme_frequency(theme_frequency, figures)
    chart_missingness(enriched, figures)

    validation = validations(frames, assignments, model_summary, outdir)
    save_csv(validation, outdir, "validation_results.csv")
    make_readme(
        outdir, enriched, reliability, correlations, model_summary,
        theme_frequency, review,
    )

    print(f"Analysis complete: {outdir}")
    print(f"Respondents: {len(analysis)}; recommended sample: {int(analysis['recommended_include'].sum())}")
    print(f"Q15 nonblank: {len(assignments)}; manual review: {len(review)}")
    print("Predictor models:")
    print(model_diagnostics[["model", "n", "r_squared"]].to_string(index=False))
    print(f"Validation checks passed: {int(validation['passed'].sum())}/{len(validation)}")


if __name__ == "__main__":
    main()
