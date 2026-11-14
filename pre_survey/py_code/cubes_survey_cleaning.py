#!/usr/bin/env python3
"""
CUBEs Pre-Project Survey - reproducible cleaning & preprocessing pipeline
=========================================================================
Usage:
    python cubes_survey_cleaning.py --input <file.xlsx> --outdir <output_dir>

Design rules
------------
* The source file is only ever read, never written.
* Original values are always preserved (raw dataset + *_raw / *_orig columns).
* Rows are NEVER dropped or imputed. Quality problems are FLAGGED in boolean
  columns; an optional recommended-analytic-sample flag is provided.
* Transformations are labelled AUTOMATIC (formatting-only, safe) or
  REVIEW (judgement call: output is produced but needs your approval).
  All decisions are written to decisions_log.csv.

Outputs (in --outdir)
---------------------
 01_raw_imported.csv              all response rows, original codes, original values
 02_cleaned_respondent_level.csv  one row per respondent, typed/standardised + flags
 03_analysis_dataset.csv          no direct identifiers / admin metadata, pseudonymous ID
 04_data_dictionary.csv           code, exact label, type, observed values, missing, transforms
 05_multiselect_indicators.csv    wide binary indicators for Q5 and Q18
 05b_multiselect_long.csv         long-format selection table
 06_skills_long.csv               tidy: respondent x skill x {Q10,Q11,Q12}
 07_data_quality_report.txt       narrative quality report
 08_linkage_RESTRICTED.csv        pseudonym <-> student ID (access-restricted!)
 decisions_log.csv                automatic vs needs-review decisions
 flagged_records_for_review.csv   records with one or more quality flags
"""
import argparse
import hashlib
import os
import re
import sys
from io import StringIO

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# CONFIGURATION (edit here, not in the code below)
# --------------------------------------------------------------------------
SHEET = "Sheet0"
SALT = os.environ.get("CUBES_SALT", "CHANGE-ME-keep-secret")  # for pseudonyms
MIN_DURATION_SEC = 60            # REVIEW: "speeder" threshold (flag only)
MAX_DURATION_SEC = 6 * 3600      # REVIEW: very long sessions (flag only)
AGE_MIN, AGE_MAX = 16, 80        # plausibility window for flagging only

# Variable groups (from the actual file's header row 1)
META_COLS = ["StartDate", "EndDate", "Status", "Progress", "Duration (in seconds)",
             "Finished", "RecordedDate", "DistributionChannel", "UserLanguage"]
DIRECT_ID_COLS = ["IPAddress", "ResponseId", "RecipientLastName", "RecipientFirstName",
                  "RecipientEmail", "ExternalReference", "LocationLatitude",
                  "LocationLongitude", "Q22"]
SKILLS = {1: "Teamwork", 2: "Research", 3: "Creativity", 4: "Critical Thinking",
          5: "Professional Writing", 6: "Public Speaking", 7: "Leadership",
          8: "Data Analysis", 9: "Computer/technological Skills"}
SKILL_QS = {"Q10": "current_proficiency", "Q11": "career_benefit", "Q12": "expected_improvement"}
MULTISELECT = {"Q5": "Q5_5_TEXT", "Q18": "Q18_8_TEXT"}
# ordinal text scales: order is taken from the OBSERVED labels in the data
ORDINAL_ORDERS = {
    "Q4": ["Very not ready", "Somewhat not ready", "Neither ready nor not ready",
           "Somewhat ready", "Very ready"],
    "Q7": ["Very unprepared", "Somewhat unprepared", "Neither prepared nor unprepared",
           "Somewhat prepared", "Very prepared"],
    "Q8": ["Seldom (less than once per year)", "Sometimes (once per year)",
           "Frequently (once per semester)", "Often (more than 2x per year)"],
    "Q9": ["Very much less qualified", "Somewhat less qualified",
           "Neither more or less qualified", "Somewhat more qualified",
           "Very much more qualified"],
    "Q14": ["Very unexcited", "Somewhat unexcited", "Neither excited nor unexcited",
            "Somewhat excited", "Very excited"],
    "Q6": ["None at all", "A little", "A moderate amount", "A lot", "A great deal"],
}

LOG = []  # decisions log


def log(step, variable, kind, description, n_affected=None):
    """kind = 'AUTOMATIC' or 'REVIEW'."""
    LOG.append(dict(step=step, variable=variable, kind=kind,
                    description=description, n_affected=n_affected))


def banner(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# --------------------------------------------------------------------------
# 1. LOAD
# --------------------------------------------------------------------------
def load(path):
    """Row 1 = variable codes, row 2 = exact question labels, rows 3+ = data."""
    raw_all = pd.read_excel(path, sheet_name=SHEET, header=None, dtype=object)
    codes = [str(c).strip() for c in raw_all.iloc[0]]
    labels = [("" if pd.isna(x) else str(x)) for x in raw_all.iloc[1]]
    if len(set(codes)) != len(codes):
        print("WARNING duplicate column codes:", [c for c in codes if codes.count(c) > 1])
    data = raw_all.iloc[2:].copy()
    data.columns = codes
    data = data.reset_index(drop=True)
    data.insert(0, "row_id", np.arange(1, len(data) + 1))  # stable internal key
    return data, dict(zip(codes, labels))


# --------------------------------------------------------------------------
# 2. INSPECT (before any transformation)
# --------------------------------------------------------------------------
def classify(code):
    if code in META_COLS:
        return "survey metadata"
    if code in DIRECT_ID_COLS:
        return "identifier / sensitive"
    if code.startswith("Recipient") or code == "ExternalReference":
        return "identifier / sensitive"
    if code.endswith("_TEXT"):
        return "free text ('Other' specify)"
    if code in MULTISELECT:
        return "multi-select (select all)"
    if re.match(r"Q(10|11|12|13)_\d+$", code):
        return "numeric rating"
    if re.match(r"Q6_\d+$", code):
        return "ordinal rating (text scale)"
    if code in ORDINAL_ORDERS:
        return "ordinal (text scale)"
    if code == "Q15":
        return "open-ended text"
    if code == "Q16":
        return "demographic: age (numeric, messy)"
    if code in ("Q17", "Q19", "Q20", "Q21"):
        return "demographic / categorical"
    if code in ("Q2", "Q3"):
        return "categorical (single choice)"
    return "other"


def inspect(df, labels):
    banner("1. INSPECTION (before any transformation)")
    print(f"Dimensions: {df.shape[0]} rows x {df.shape[1] - 1} survey columns")
    print("Empty columns:", [c for c in df.columns if df[c].isna().all()])
    print("Empty rows:", int(df.drop(columns="row_id").isna().all(axis=1).sum()))
    print("Exact duplicate rows:", int(df.drop(columns="row_id").duplicated().sum()))
    print("Duplicate ResponseId:", int(df["ResponseId"].duplicated().sum()))
    q22 = df["Q22"].dropna().astype(str).str.strip()
    print("Duplicate non-missing Q22 values:", int(q22.duplicated().sum()),
          "(students appearing >1 time)")
    miss = df.isna().sum()
    summ = pd.DataFrame({"type": [classify(c) for c in df.columns if c != "row_id"],
                         "n_missing": miss.drop("row_id").values,
                         "pct_missing": (miss.drop("row_id") / len(df) * 100).round(1).values,
                         "n_unique": df.drop(columns="row_id").nunique().values},
                        index=[c for c in df.columns if c != "row_id"])
    with pd.option_context("display.max_rows", 200, "display.width", 200):
        print(summ)
    print("\nSample rows:")
    print(df[["row_id", "StartDate", "Progress", "Finished", "Q2", "Q4", "Q10_1", "Q16"]].head(5))
    return summ


# --------------------------------------------------------------------------
# 3. TYPE CONVERSION & STANDARDISATION
# --------------------------------------------------------------------------
def to_bool(s):
    return s.astype(str).str.strip().str.lower().map({"true": True, "false": False})


def parse_age(s):
    """Return numeric age from messy text. Only extracts a clean 1-3 digit number."""
    def f(v):
        if pd.isna(v):
            return np.nan
        m = re.fullmatch(r"\D*?(\d{1,3})\D*", str(v).strip())
        return float(m.group(1)) if m else np.nan
    return s.map(f)


GENDER_PROPOSED = {  # REVIEW: semantic recode, kept separate from raw
    "male": "Male", "m": "Male", "man": "Male", "boy": "Male",
    "female": "Female", "f": "Female", "woman": "Female", "girl": "Female",
}


def clean(df, labels):
    banner("2. CLEANING / STANDARDISATION")
    c = df.copy()

    # --- 3a. whitespace/tab trimming on all text (AUTOMATIC, formatting only) ---
    n_changed = {}
    for col in c.columns:
        if col == "row_id" or c[col].dtype != object:
            continue
        s = c[col]
        stripped = s.map(lambda v: re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v)
        changed = int(((s != stripped) & s.notna()).sum())
        if changed:
            c[col + "_orig"] = s  # preserve original only where something changed
            c[col] = stripped
            n_changed[col] = changed
    for k, v in n_changed.items():
        log("whitespace", k, "AUTOMATIC", "Trimmed leading/trailing/embedded tab+space; "
            f"original kept in {k}_orig", v)
    print("Whitespace-trimmed columns:", n_changed)

    # --- 3b. datetimes ---
    for col in ["StartDate", "EndDate", "RecordedDate"]:
        c[col] = pd.to_datetime(c[col], errors="coerce")
    log("types", "StartDate/EndDate/RecordedDate", "AUTOMATIC", "Converted to datetime")
    print("Date range:", c["StartDate"].min(), "->", c["StartDate"].max(),
          "| invalid dates:", int(c["StartDate"].isna().sum()))

    # --- 3c. numeric metadata & ratings ---
    c["Progress"] = pd.to_numeric(c["Progress"], errors="coerce")
    c["Duration (in seconds)"] = pd.to_numeric(c["Duration (in seconds)"], errors="coerce")
    c["Finished"] = to_bool(c["Finished"])
    log("types", "Finished", "AUTOMATIC", "Stored as text 'True'/'False' in file; converted to boolean")
    rating_cols = [f"{q}_{i}" for q in ("Q10", "Q11", "Q12") for i in SKILLS] + ["Q13_1"]
    for col in rating_cols:
        raw = c[col]
        c[col] = pd.to_numeric(raw, errors="coerce")
        bad = int((raw.notna() & c[col].isna()).sum())
        if bad:
            print(f"  non-numeric values in {col}: {bad}")
    obs = {}
    for q in ("Q10", "Q11", "Q12", "Q13"):
        cols = [x for x in rating_cols if x.startswith(q)]
        obs[q] = sorted(pd.unique(c[cols].values.ravel()[~pd.isna(c[cols].values.ravel())]))
    print("Observed numeric rating values:", obs)
    log("ratings", "Q10-Q13", "REVIEW",
        f"Observed values {obs}. The file stores only numeric codes (no scale anchors), so the "
        "meaning/direction of 0-5 cannot be verified from the file. Values 0 appear in Q10_6, "
        "Q12, Q13 (not in all items). Kept as-is; please confirm anchors from the Qualtrics survey.")

    # --- 3d. age ---
    c["Q16_raw"] = c["Q16"]
    c["age"] = parse_age(c["Q16"])
    c["age_implausible"] = c["age"].notna() & ~c["age"].between(AGE_MIN, AGE_MAX)
    c["age_unparsed"] = c["Q16"].notna() & c["age"].isna()
    log("age", "Q16", "AUTOMATIC", "Extracted numeric age into `age` where cell is a number "
        "optionally with stray text (e.g. '22 years old.', '`22'); raw kept in Q16_raw",
        int((c["Q16"].notna() & (c["Q16"].astype(str).str.fullmatch(r"\d+") == False)).sum()))
    log("age", "Q16", "REVIEW", "Non-numeric responses (e.g. 'X') left as NaN in `age` and flagged "
        "in age_unparsed; ages outside plausibility window flagged in age_implausible")
    print("Age summary:\n", c["age"].describe().round(1).to_string())
    print("Unparsed:", c.loc[c["age_unparsed"], "Q16_raw"].tolist())

    # --- 3e. ordinal text scales -> ordered categoricals + numeric codes ---
    for q, order in ORDINAL_ORDERS.items():
        cols = [x for x in c.columns if x == q or re.fullmatch(rf"{q}_\d+", x)]
        for col in cols:
            vals = set(c[col].dropna().unique())
            unexpected = vals - set(order)
            if unexpected:
                print(f"  {col}: values not in expected order list: {unexpected}")
            c[col + "_ord"] = pd.Categorical(c[col], categories=order, ordered=True).codes
            c.loc[c[col].isna(), col + "_ord"] = np.nan
            c[col + "_ord"] = c[col + "_ord"].replace(-1, np.nan)
    log("ordinal", "Q4,Q6,Q7,Q8,Q9,Q14", "REVIEW",
        "Text labels retained; added *_ord columns (0..k-1 following the label order observed "
        "in the data). Confirm the label ordering and whether the neutral midpoint is appropriate.")

    # --- 3f. gender (Q17): case/whitespace automatic, semantic recode REVIEW ---
    c["Q17_raw"] = c["Q17"]
    key = c["Q17"].str.strip().str.lower()
    c["Q17_proposed"] = key.map(GENDER_PROPOSED)
    c.loc[key.notna() & c["Q17_proposed"].isna(), "Q17_proposed"] = "Other/unmapped (review)"
    log("gender", "Q17", "REVIEW",
        "Q17 is free text. Proposed recode in Q17_proposed (male/m/man->Male, female/f/woman/girl->Female; "
        "everything else 'Other/unmapped (review)'); Q17 itself is unchanged. Approve mapping or edit "
        "GENDER_PROPOSED.", int(c["Q17_proposed"].notna().sum()))
    print("Q17 raw:", c["Q17_raw"].value_counts(dropna=False).to_dict())
    print("Q17 proposed:", c["Q17_proposed"].value_counts(dropna=False).to_dict())

    # --- 3g. Q21 class: numeric codes are unlabelled ---
    c["Q21_is_numeric_code"] = c["Q21"].astype(str).str.fullmatch(r"\d+") & c["Q21"].notna()
    log("class", "Q21", "REVIEW",
        "Some waves exported choice codes (e.g. 5, 6, 7, 11, 15, 20) instead of labels. Codes cannot "
        "be mapped to class names from this file; flagged in Q21_is_numeric_code. Provide the "
        "code-to-class key or use 'Use choice text' in the Qualtrics export.",
        int(c["Q21_is_numeric_code"].sum()))

    # --- 3h. wave (survey administration period) ---
    c["wave_year"] = c["StartDate"].dt.year
    c["wave_month"] = c["StartDate"].dt.to_period("M").astype(str)
    log("wave", "StartDate", "REVIEW",
        "Responses span 2022-2026 across multiple administrations. wave_year/wave_month derived from "
        "StartDate; define semesters/waves explicitly (e.g. Spring = Jan-May) before comparing cohorts. "
        "Late stragglers (e.g. Jun/Jul/Dec) need an assignment rule.")
    return c


# --------------------------------------------------------------------------
# 4. MISSINGNESS / QUALITY FLAGS
# --------------------------------------------------------------------------
def quality_flags(c):
    banner("3. COMPLETENESS & QUALITY FLAGS (nothing is deleted)")
    core = ([f"{q}_{i}" for q in ("Q10", "Q11", "Q12") for i in SKILLS]
            + ["Q4", "Q7", "Q8", "Q9", "Q13_1", "Q14"])
    c["n_core_answered"] = c[core].notna().sum(axis=1)
    c["core_pct_answered"] = (c["n_core_answered"] / len(core) * 100).round(1)
    dur = c["Duration (in seconds)"]
    c["flag_not_finished"] = c["Finished"] == False                         # noqa: E712
    c["flag_progress_lt100"] = c["Progress"] < 100
    c["flag_no_core_items"] = c["n_core_answered"] == 0
    c["flag_speeder"] = dur < MIN_DURATION_SEC
    c["flag_very_long"] = dur > MAX_DURATION_SEC
    # straight-lining: identical answer across all 9 skills for a given question block
    for q in ("Q10", "Q11", "Q12"):
        blk = c[[f"{q}_{i}" for i in SKILLS]]
        c[f"flag_straightline_{q}"] = (blk.notna().all(axis=1)) & (blk.nunique(axis=1) == 1)
    # ID problems
    q22 = c["Q22"].astype(str).str.strip()
    has = c["Q22"].notna()
    c["flag_q22_dup_in_file"] = has & c["Q22"].duplicated(keep=False)
    c["flag_q22_nonstandard"] = has & ~q22.str.fullmatch(r"\d{8}")
    c["flag_dup_response_id"] = c["ResponseId"].duplicated(keep=False)
    # Exact duplicate of all answers (excluding metadata) -> flag only
    answer_cols = [x for x in c.columns if re.match(r"Q\d+(_\d+)?(_TEXT)?$", x) and x != "Q22"]
    ans = c[answer_cols].astype(str)
    has_ans = c[answer_cols].notna().sum(axis=1) > 3
    c["flag_identical_answers"] = has_ans & ans.duplicated(keep=False)
    # Structural (version-dependent) missingness
    c["q3_not_in_version"] = c["StartDate"] < pd.Timestamp("2024-01-01")
    c["q6_not_in_version"] = c["StartDate"] < pd.Timestamp("2025-02-01")
    flag_cols = [x for x in c.columns if x.startswith("flag_")]
    c["any_flag"] = c[flag_cols].any(axis=1)

    # Recommended analytic sample - a PROPOSAL, not applied to the data
    c["recommended_include"] = (c["Finished"] == True) & (c["n_core_answered"] >= 0.8 * len(core)) \
        & ~c["flag_speeder"]                                                  # noqa: E712
    print("Flag counts:\n", c[flag_cols].sum().to_string())
    print("Recommended analytic sample (proposal):", int(c["recommended_include"].sum()),
          "of", len(c))
    print("Finished by Progress:\n", c.groupby("Finished")["Progress"].agg(["min", "max", "count"]))
    print("Duration (s), finished only:\n",
          c.loc[c["Finished"] == True, "Duration (in seconds)"]            # noqa: E712
          .describe(percentiles=[.01, .05, .5, .95]).round(0).to_string())
    log("exclusion", "recommended_include", "REVIEW",
        "PROPOSED analytic sample: Finished==True AND >=80% of 33 core items answered AND "
        f"duration >= {MIN_DURATION_SEC}s. No rows removed; filter on this column if you agree. "
        "Partially completed responses are retained in the cleaned dataset.",
        int(c["recommended_include"].sum()))
    log("duplicates", "Q22", "REVIEW",
        "Repeated Q22 values mostly span different dates/waves (retakes or repeat enrolment), not "
        "double-submissions. Not removed; flag_q22_dup_in_file marks them. Decide whether to keep first, "
        "last, or the most complete response per student for pre/post matching.",
        int(c["flag_q22_dup_in_file"].sum()))
    log("quality", "age/Q22/Q21", "REVIEW", "See flags: age_implausible, age_unparsed, "
        "flag_q22_nonstandard, Q21_is_numeric_code")
    return c


# --------------------------------------------------------------------------
# 5. MULTI-SELECT
# --------------------------------------------------------------------------
def slug(s):
    return re.sub(r"[^0-9a-zA-Z]+", "_", s).strip("_").lower()[:40]


def multiselect(c, labels):
    banner("4. MULTI-SELECT QUESTIONS")
    wide = c[["row_id"]].copy()
    long_rows = []
    for q, other_col in MULTISELECT.items():
        s = c[q]
        tokens = s.dropna().astype(str).str.split(",").explode().str.strip()
        tokens = tokens[tokens != ""]
        options = list(tokens.value_counts().index)
        print(f"{q}: stored as comma-separated labels; options observed = {options}")
        multi = int(s.dropna().astype(str).str.contains(",").sum())
        print(f"   respondents with >1 selection: {multi} of {int(s.notna().sum())}")
        if multi == 0:
            print(f"   NOTE: {q} is labelled 'select all' but every response has exactly one option.")
            log("multiselect", q, "REVIEW",
                "Labelled select-all but no cell has more than one selection (a respondent also wrote "
                "that 'select all apply doesn't work' in Q18_8_TEXT). Treat as single-choice or "
                "verify the Qualtrics question type.")
        per_resp = s.fillna("").astype(str).map(lambda v: {t.strip() for t in v.split(",") if t.strip()})
        answered = s.notna()
        for opt in options:
            col = f"{q}__{slug(opt)}"
            ind = per_resp.map(lambda st: opt in st).astype(float)
            ind[~answered] = np.nan          # unanswered != not selected
            wide[col] = ind
            long_rows.append(pd.DataFrame({"row_id": c["row_id"][answered],
                                           "question": q, "option": opt,
                                           "selected": ind[answered].astype(int)}))
        wide[f"{q}__n_selected"] = per_resp.map(len).where(answered)
        # 'Other' text
        other_opt = [o for o in options if o.lower().startswith("other") or "self-describe" in o.lower()]
        wide[f"{q}__other_text"] = c[other_col]
        mism = int((c[other_col].notna() & ~per_resp.map(
            lambda st: any(o in st for o in other_opt))).sum()) if other_opt else 0
        print(f"   'Other' text present without 'Other' option selected: {mism}")
        log("multiselect", q, "AUTOMATIC",
            f"Created binary indicators {q}__* (1/0; NaN where question unanswered); original column kept. "
            f"'Other' text kept verbatim in {q}__other_text")
    long = pd.concat(long_rows, ignore_index=True)
    # Q5 'None of the above' should be exclusive
    if "Q5__none_of_the_above" in wide:
        both = ((wide["Q5__none_of_the_above"] == 1) & (wide["Q5__n_selected"] > 1)).sum()
        print("Q5 'None of the above' combined with other options:", int(both))
    return wide, long


# --------------------------------------------------------------------------
# 6. LONG-FORMAT SKILLS
# --------------------------------------------------------------------------
def skills_long(c, labels):
    banner("5. LONG-FORMAT SKILL DATASET")
    parts = []
    for q, measure in SKILL_QS.items():
        for i, name in SKILLS.items():
            code = f"{q}_{i}"
            parts.append(pd.DataFrame({
                "row_id": c["row_id"], "wave_year": c["wave_year"], "measure": measure,
                "question": q, "item_code": code, "skill": name,
                "value": c[code], "original_label": labels.get(code, "")}))
    long = pd.concat(parts, ignore_index=True)
    long["answered"] = long["value"].notna()
    wide = long.pivot_table(index=["row_id", "skill"], columns="measure", values="value",
                            aggfunc="first").reset_index()
    print("Long rows:", len(long), "| non-missing values:", int(long["answered"].sum()))
    print(long.groupby(["measure", "skill"])["value"].agg(["count", "mean"]).round(2).head(9))
    return long, wide


# --------------------------------------------------------------------------
# 7. PRIVACY / ANALYSIS DATASET
# --------------------------------------------------------------------------
def pseudonym(v):
    return "P" + hashlib.sha256((SALT + v).encode()).hexdigest()[:10]


def privacy(c):
    banner("6. PRIVACY SEPARATION")
    sid = c["Q22"].astype(str).str.strip()
    # Pseudonymise only digit-only IDs of 6-9 digits; free text / emails / 16-digit numbers are NOT
    ok = c["Q22"].notna() & sid.str.fullmatch(r"\d{6,9}")
    c["pseudo_id"] = sid.where(ok).map(lambda v: pseudonym(v) if isinstance(v, str) else np.nan)
    print("Pseudonymised IDs:", int(ok.sum()), "| Q22 present but not pseudonymised:",
          int((c["Q22"].notna() & ~ok).sum()))
    log("privacy", "Q22", "REVIEW",
        "Q22 holds student IDs but ALSO an email, a name, free text and 16-digit numbers. Only digit "
        "strings of 6-9 characters get a salted-hash pseudonym; others are left without one and listed "
        "for manual review. IDs with 6/7/9 digits or leading-zero differences are NOT auto-corrected; "
        "set CUBES_SALT env var before running.", int((~ok & c["Q22"].notna()).sum()))
    linkage = c.loc[ok, ["row_id", "pseudo_id", "Q22", "StartDate"]].rename(columns={"Q22": "student_id"})

    drop = (DIRECT_ID_COLS + ["Q22_orig", "StartDate", "EndDate", "RecordedDate", "Status",
            "DistributionChannel", "UserLanguage", "Q16", "Q16_raw", "Q17_raw", "Q21_orig"]
            + [x for x in c.columns if x.endswith("_orig")])
    analysis = c.drop(columns=[x for x in set(drop) if x in c.columns]).copy()
    # keep date info only at coarse level (wave_year/wave_month already present)
    analysis = analysis.drop(columns=["wave_month"], errors="ignore").assign(
        wave_month=c["StartDate"].dt.to_period("M").astype(str))
    log("privacy", "IPAddress, lat/long, ResponseId, names, email, ExternalReference", "AUTOMATIC",
        "Removed from analysis dataset (kept in cleaned respondent-level file). Exact timestamps replaced "
        "by wave_year/wave_month.")
    log("privacy", "Q15, *_TEXT, Q21", "REVIEW",
        "Open-ended/'Other' text and instructor names in Q21 can identify people; retained in the "
        "analysis dataset but should be screened before sharing/publishing quotes.")
    print("Analysis dataset columns:", analysis.shape[1])
    return c, analysis, linkage


# --------------------------------------------------------------------------
# 8. DATA DICTIONARY
# --------------------------------------------------------------------------
def dictionary(raw, c, labels, transforms):
    rows = []
    for code in [x for x in raw.columns if x != "row_id"]:
        s = raw[code]
        vc = s.dropna().astype(str).value_counts()
        observed = "; ".join(f"{k} (n={v})" for k, v in vc.head(12).items())
        if len(vc) > 12:
            observed += f"; ... {len(vc)} distinct values"
        rows.append(dict(
            variable_code=code, original_label=labels.get(code, ""), variable_type=classify(code),
            n_missing=int(s.isna().sum()), pct_missing=round(s.isna().mean() * 100, 1),
            n_unique=int(s.nunique()), observed_values=observed,
            transformations=transforms.get(code, "none"),
            display_label=display_label(code, labels.get(code, "")),
            is_identifier=code in DIRECT_ID_COLS))
    return pd.DataFrame(rows)


def display_label(code, label):
    """Short readable label for plots (original question kept in original_label)."""
    m = re.match(r"(Q(?:10|11|12))_(\d+)$", code)
    if m:
        pre = {"Q10": "Proficiency", "Q11": "Career benefit", "Q12": "Expected improvement"}[m.group(1)]
        return f"{pre}: {SKILLS[int(m.group(2))]}"
    m = re.match(r"Q6_(\d+)$", code)
    if m:
        names = {1: "Research project", 2: "Real-organization project", 3: "Case study", 4: "Business plan"}
        return f"Career contribution: {names[int(m.group(1))]}"
    simple = {"Q2": "Currently working", "Q3": "Job in chosen field", "Q4": "Workforce readiness",
              "Q5": "Prior course activities", "Q7": "Coursework preparedness",
              "Q8": "Networking frequency", "Q9": "Qualifications vs. others",
              "Q13_1": "Looking forward to project", "Q14": "Excitement: CUBEs project",
              "Q15": "Hopes for course", "Q16": "Age", "Q17": "Gender", "Q18": "Race/ethnicity",
              "Q19": "First-generation", "Q20": "Low-income", "Q21": "Class/professor",
              "Q22": "Student ID"}
    return simple.get(code, label[:50])


# --------------------------------------------------------------------------
# 9. REPORT
# --------------------------------------------------------------------------
def report(raw, c, summ):
    n = len(c)
    out = StringIO()
    p = lambda *a: print(*a, file=out)
    p("CUBEs PRE-PROJECT SURVEY - DATA QUALITY REPORT")
    p("=" * 60)
    p(f"Respondent rows: {n} | survey columns: {raw.shape[1] - 1}")
    p(f"Date range: {c['StartDate'].min()} to {c['StartDate'].max()}")
    p("Responses per year:", c["wave_year"].value_counts().sort_index().to_dict())
    p("\nCOMPLETENESS")
    p(f"  Finished=True: {int((c['Finished'] == True).sum())} | Finished=False: {int((c['Finished'] == False).sum())}")  # noqa
    p(f"  Respondents with zero core items answered: {int(c['flag_no_core_items'].sum())}")
    p(f"  Proposed analytic sample (recommended_include): {int(c['recommended_include'].sum())}")
    p("\nEMPTY COLUMNS (100% missing): " +
      ", ".join(summ.index[summ.pct_missing == 100]))
    p("\nSTRUCTURAL MISSINGNESS (not item non-response)")
    p(f"  Q3 absent from survey before 2024: {int(c['q3_not_in_version'].sum())} rows; also only asked of "
      "people who work (Q2 = yes, full/part-time)")
    p(f"  Q6 absent from survey before Feb 2025: {int(c['q6_not_in_version'].sum())} rows; and only partly "
      "associated with Q5 selections")
    p("  Q*_TEXT columns are blank unless 'Other' was chosen (legitimate skip)")
    p("\nDUPLICATES")
    p(f"  exact duplicate rows: {int(raw.drop(columns='row_id').duplicated().sum())}; "
      f"duplicate ResponseId: {int(c['flag_dup_response_id'].sum())}; "
      f"rows sharing a Q22 value: {int(c['flag_q22_dup_in_file'].sum())}; "
      f"rows with identical answer pattern: {int(c['flag_identical_answers'].sum())}")
    p("\nFLAG COUNTS")
    for col in [x for x in c.columns if x.startswith("flag_")] + ["age_implausible", "age_unparsed",
                                                                  "Q21_is_numeric_code"]:
        p(f"  {col}: {int(c[col].sum())}")
    p("\nDECISIONS (see decisions_log.csv)")
    for d in LOG:
        p(f"  [{d['kind']}] {d['variable']}: {d['description']}")
    return out.getvalue()


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="cubes_output")
    a = ap.parse_args()
    if not os.path.exists(a.input):
        sys.exit(f"Input not found: {a.input}")
    os.makedirs(a.outdir, exist_ok=True)

    raw, labels = load(a.input)
    summ = inspect(raw, labels)
    c = clean(raw, labels)
    c = quality_flags(c)
    wide, mlong = multiselect(c, labels)
    c = c.merge(wide, on="row_id", how="left")
    slong, _ = skills_long(c, labels)
    c, analysis, linkage = privacy(c)

    transforms = {"Q16": "age parsed to `age`; raw in Q16_raw", "Q17": "proposed recode Q17_proposed",
                  "Q21": "numeric-code flag", "Finished": "text->boolean", "Q22": "pseudonymised",
                  "Q4": "whitespace/tab trimmed; ordinal code Q4_ord", "Q7": "whitespace trimmed; Q7_ord",
                  "Q5": "indicator columns Q5__*", "Q18": "indicator columns Q18__*"}
    dd = dictionary(raw, c, labels, transforms)

    out = lambda n: os.path.join(a.outdir, n)
    raw.to_csv(out("01_raw_imported.csv"), index=False)
    c.to_csv(out("02_cleaned_respondent_level.csv"), index=False)
    analysis.to_csv(out("03_analysis_dataset.csv"), index=False)
    dd.to_csv(out("04_data_dictionary.csv"), index=False)
    c[["row_id"] + [x for x in c.columns if "__" in x]].to_csv(out("05_multiselect_indicators.csv"), index=False)
    mlong.to_csv(out("05b_multiselect_long.csv"), index=False)
    slong.to_csv(out("06_skills_long.csv"), index=False)
    linkage.to_csv(out("08_linkage_RESTRICTED.csv"), index=False)
    pd.DataFrame(LOG).to_csv(out("decisions_log.csv"), index=False)
    flagged = c[c["any_flag"] | c["age_implausible"] | c["age_unparsed"]]
    flagged[["row_id", "wave_month", "Progress", "Duration (in seconds)", "n_core_answered"]
            + [x for x in c.columns if x.startswith("flag_")]].to_csv(
        out("flagged_records_for_review.csv"), index=False)
    with open(out("07_data_quality_report.txt"), "w") as f:
        f.write(report(raw, c, summ))
    banner("DONE")
    print("Files written to", os.path.abspath(a.outdir))
    print("Decisions needing your review:", sum(d["kind"] == "REVIEW" for d in LOG))


if __name__ == "__main__":
    main()
