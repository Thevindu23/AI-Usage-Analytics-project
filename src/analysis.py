"""Reproducible cleaning and exploratory analysis of the AI-usage survey dataset.

Run from anywhere with:
    python -m src.analysis
when your working directory is the repository root.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Save charts without requiring a GUI.
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data/raw/AI_Usage_and_Impact_on_Students_and_Professionals.csv"
CLEAN_CSV = ROOT / "data/processed/AI_Usage_Cleaned.csv"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

EXPECTED_COLUMNS = [
    "User_ID", "Age", "Gender", "Country", "User_Type", "Education_Level",
    "Profession", "Monthly_Income", "AI_Tool", "AI_Purpose",
    "AI_Usage_Hours_Per_Day", "Tasks_Performed", "Monthly_AI_Cost",
    "Productivity_Score", "Accuracy_Rating", "Satisfaction_Score",
    "Time_Saved_Hours_Per_Week", "Work_or_Study_Hours_Per_Day",
    "Would_Recommend",
]

TEXT_NUMERIC_COLUMNS = [
    "Age", "Monthly_Income", "AI_Usage_Hours_Per_Day", "Monthly_AI_Cost",
    "Time_Saved_Hours_Per_Week", "Work_or_Study_Hours_Per_Day",
]

TOOL_ALIASES = {
    "chatgpt": "ChatGPT", "chat gpt": "ChatGPT",
    "gemini": "Google Gemini", "google gemini": "Google Gemini",
    "copilot": "Microsoft Copilot", "microsoft copilot": "Microsoft Copilot",
    "claude": "Claude", "deepseek": "DeepSeek", "meta ai": "Meta AI",
    "perplexity ai": "Perplexity AI", "grammarly": "Grammarly",
}

EDUCATION_ALIASES = {
    "undergrad": "Undergraduate", "undergraduate": "Undergraduate",
    "bachelors": "Bachelor's", "bachelor's": "Bachelor's",
    "bachelor's degree": "Bachelor's", "ba/bsc": "Bachelor's",
    "masters": "Master's", "master's": "Master's",
    "master's degree": "Master's", "ma/msc": "Master's",
    "high school": "High School", "hs": "High School",
    "phd": "PhD", "ph.d.": "PhD", "diploma": "Diploma",
}


def read_raw_data(path: Path = RAW_CSV) -> pd.DataFrame:
    """Load the raw data while checking for accidental schema changes."""
    df = pd.read_csv(path)
    missing_columns = sorted(set(EXPECTED_COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")
    return df


def _parse_numeric(series: pd.Series) -> pd.Series:
    """Convert a number with optional unit/currency punctuation; leave failures missing.

    Examples: '2 hrs' -> 2, '28 yrs' -> 28, '$20' -> 20.
    This transformation does not impute missing values or remove outliers.
    """
    values = (
        series.astype("string")
        .str.strip()
        .str.replace(r"(?i)\s*(?:hours?|hrs?|years?|yrs?)\s*$", "", regex=True)
        .str.replace(r"[$,]", "", regex=True)
        .str.strip()
    )
    return pd.to_numeric(values, errors="coerce")


def clean_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicates, standardize known labels, and parse numeric fields."""
    df = raw.drop_duplicates().copy().reset_index(drop=True)

    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = df[column].astype("string").str.strip().replace("", pd.NA)

    df["AI_Tool"] = (
        df["AI_Tool"].str.lower().map(TOOL_ALIASES).fillna(df["AI_Tool"]).astype("string")
    )
    df["Gender"] = (
        df["Gender"].str.lower()
        .replace({"m": "male", "f": "female"})
        .str.title()
    )
    df["Country"] = (
        df["Country"].str.title()
        .replace({"U.K.": "United Kingdom", "United States Of America": "United States"})
    )
    df["Education_Level"] = (
        df["Education_Level"].str.lower()
        .map(EDUCATION_ALIASES)
        .fillna(df["Education_Level"])
        .astype("string")
    )
    for column in ["User_Type", "AI_Purpose", "Would_Recommend"]:
        df[column] = df[column].str.title()

    for column in TEXT_NUMERIC_COLUMNS:
        df[column] = _parse_numeric(df[column])
    for column in ["Productivity_Score", "Accuracy_Rating", "Satisfaction_Score"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def data_quality_report(raw: pd.DataFrame, clean: pd.DataFrame) -> pd.DataFrame:
    """Column-by-column completeness before and after exact-duplicate removal."""
    rows = []
    for col in EXPECTED_COLUMNS:
        rows.append({
            "Column": col,
            "Original_Missing": int(raw[col].isna().sum()),
            "Cleaned_Missing": int(clean[col].isna().sum()),
            "Cleaned_Missing_Pct": round(100 * clean[col].isna().mean(), 2),
            "Cleaned_Dtype": str(clean[col].dtype),
            "Cleaned_Unique": int(clean[col].nunique(dropna=True)),
        })
    return pd.DataFrame(rows)


def user_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("User_Type", dropna=False)
        .agg(
            Respondents=("User_ID", "count"),
            Median_Daily_AI_Hours=("AI_Usage_Hours_Per_Day", "median"),
            Mean_Productivity=("Productivity_Score", "mean"),
            Mean_Weekly_Time_Saved=("Time_Saved_Hours_Per_Week", "mean"),
            Valid_Time_Saved=("Time_Saved_Hours_Per_Week", "count"),
        )
        .round(2)
    )


def tool_time_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("AI_Tool")["Time_Saved_Hours_Per_Week"]
        .agg(Valid_Responses="count", Mean_Hours="mean", Median_Hours="median")
        .sort_values("Mean_Hours", ascending=False)
        .round(2)
    )


def spending_summary(df: pd.DataFrame) -> pd.DataFrame:
    known = df.loc[df["Monthly_AI_Cost"].notna()].copy()
    known["Spending_Group"] = "Reported cost > 0"
    known.loc[known["Monthly_AI_Cost"] == 0, "Spending_Group"] = "No reported cost"
    return (
        known.groupby("Spending_Group")["Satisfaction_Score"]
        .agg(Valid_Responses="count", Mean_Satisfaction="mean")
        .round(2)
    )


def recommendation_summary(df: pd.DataFrame) -> pd.DataFrame:
    """'Yes' recommendation rate conditional on nonmissing satisfaction and intent."""
    valid = df[["Satisfaction_Score", "Would_Recommend"]].dropna().copy()
    valid["Satisfaction_Group"] = pd.cut(
        valid["Satisfaction_Score"],
        bins=[float("-inf"), 5, 7, float("inf")],
        labels=["Low (<=5)", "Moderate (6–7)", "High (>=8)"],
    )
    valid["Is_Yes"] = valid["Would_Recommend"].eq("Yes")
    return (
        valid.groupby("Satisfaction_Group", observed=True)["Is_Yes"]
        .agg(Valid_Responses="count", Yes_Rate="mean")
        .assign(Yes_Rate=lambda t: (t["Yes_Rate"] * 100).round(1))
    )


def _save(fig: plt.Figure, filename: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES / filename, dpi=170, bbox_inches="tight")
    plt.close(fig)


def generate_charts(df: pd.DataFrame) -> None:
    """Recreate six publication-ready, labeled charts from the cleaned data."""
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    # Chart 1: all named tools (missing labels excluded).
    tools = df["AI_Tool"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(9, 5.2))
    bars = ax.barh(tools.index, tools.values)
    ax.bar_label(bars, padding=3)
    ax.set_xlim(0, max(tools.values) * 1.15)
    ax.set_title("Most Reported AI Tools")
    ax.set_xlabel("Number of respondents")
    ax.set_ylabel("")
    _save(fig, "01_ai_tool_popularity.png")

    # Chart 2: reported time-savings by respondent group.
    comparison = user_type_summary(df).sort_index()
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    bars = ax.bar(comparison.index, comparison["Mean_Weekly_Time_Saved"])
    ax.bar_label(bars, labels=[f"{v:.2f} h (n={int(n)})" for v, n in zip(
        comparison["Mean_Weekly_Time_Saved"], comparison["Valid_Time_Saved"]
    )], padding=5)
    ax.set_ylim(0, comparison["Mean_Weekly_Time_Saved"].max() * 1.24)
    ax.set_title("Average Self-Reported Weekly Time Savings")
    ax.set_ylabel("Hours saved per week (mean)")
    _save(fig, "02_time_saved_by_user_type.png")

    # Chart 3: daily AI hours and reported productivity.
    paired = df[["User_Type", "AI_Usage_Hours_Per_Day", "Productivity_Score"]].dropna()
    fig, ax = plt.subplots(figsize=(8.5, 5.3))
    for group, subset in paired.groupby("User_Type"):
        ax.scatter(subset["AI_Usage_Hours_Per_Day"], subset["Productivity_Score"],
                   alpha=0.62, label=f"{group} (n={len(subset)})")
    corr = paired["AI_Usage_Hours_Per_Day"].corr(paired["Productivity_Score"])
    ax.text(0.98, 0.04, f"Pearson r = {corr:.2f}", ha="right", va="bottom", transform=ax.transAxes)
    ax.set_title("Daily AI Use vs Reported Productivity")
    ax.set_xlabel("AI usage (hours per day)")
    ax.set_ylabel("Reported productivity score")
    ax.legend(loc="upper left")
    _save(fig, "03_usage_vs_productivity.png")

    # Chart 4: compare only tools with at least five valid time-savings responses.
    tool_summary = tool_time_summary(df)
    eligible = tool_summary[tool_summary["Valid_Responses"] >= 5].sort_values("Mean_Hours")
    fig, ax = plt.subplots(figsize=(9, 5.3))
    labels = [f"{tool}  (n={int(n)})" for tool, n in zip(eligible.index, eligible["Valid_Responses"])]
    bars = ax.barh(labels, eligible["Mean_Hours"])
    ax.bar_label(bars, labels=[f"{v:.2f}" for v in eligible["Mean_Hours"]], padding=3)
    ax.set_xlim(0, eligible["Mean_Hours"].max() * 1.2)
    ax.set_title("Reported Time Saved by AI Tool (n ≥ 5)")
    ax.set_xlabel("Mean hours saved per week")
    _save(fig, "04_time_saved_by_tool.png")

    # Chart 5: no reported cost vs greater-than-zero reported cost.
    spending = spending_summary(df)
    ordered = ["No reported cost", "Reported cost > 0"]
    spending = spending.reindex(ordered)
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    bars = ax.bar(spending.index, spending["Mean_Satisfaction"])
    ax.bar_label(bars, labels=[f"{v:.2f} (n={int(n)})" for v, n in zip(
        spending["Mean_Satisfaction"], spending["Valid_Responses"]
    )], padding=5)
    ax.set_ylim(0, 10)
    ax.set_title("Mean Satisfaction by Reported AI Spending")
    ax.set_ylabel("Satisfaction score (mean)")
    _save(fig, "05_satisfaction_by_spending.png")

    # Chart 6: recommend-'Yes' share among valid scores/replies.
    recommendations = recommendation_summary(df)
    fig, ax = plt.subplots(figsize=(8.3, 4.8))
    bars = ax.bar(recommendations.index.astype(str), recommendations["Yes_Rate"])
    ax.bar_label(bars, labels=[f"{rate:.1f}% (n={int(n)})" for rate, n in zip(
        recommendations["Yes_Rate"], recommendations["Valid_Responses"]
    )], padding=5)
    ax.set_ylim(0, 100)
    ax.set_title("Recommendation Rate by Satisfaction Band")
    ax.set_ylabel("Percent answering 'Yes'")
    _save(fig, "06_recommendation_by_satisfaction.png")


def main() -> None:
    raw = read_raw_data()
    cleaned = clean_data(raw)
    CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(CLEAN_CSV, index=False)
    data_quality_report(raw, cleaned).to_csv(REPORTS / "data_quality_report.csv", index=False)
    generate_charts(cleaned)

    paired = cleaned[["AI_Usage_Hours_Per_Day", "Productivity_Score"]].dropna()
    corr_all = paired.corr().iloc[0, 1]
    corr_no_extreme = paired.loc[paired["AI_Usage_Hours_Per_Day"] <= 16].corr().iloc[0, 1]
    print(f"Original rows: {len(raw)}")
    print(f"Exact duplicates removed: {raw.duplicated().sum()}")
    print(f"Rows after cleaning: {len(cleaned)}")
    print(f"Most reported tool: {cleaned['AI_Tool'].value_counts().idxmax()}")
    print(f"Pearson correlation (all valid pairs): {corr_all:.3f}")
    print(f"Pearson correlation (excluding >16 h/day): {corr_no_extreme:.3f}")
    print(f"Wrote cleaned data, quality report, and six figures under: {ROOT}")


if __name__ == "__main__":
    main()
