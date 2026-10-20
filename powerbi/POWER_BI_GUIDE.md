# Power BI dashboard — Setup and explanation

## What you get

An editable Power BI Desktop **project** (`AI_Usage_Dashboard.pbip`) with two report pages, built-in measures, model fields, charts, KPI cards and slicers. The cleaned 288-row CSV is embedded into the Power Query M import source as base64 so the report does **not require a hard-coded Windows file path**.

### Pages

1. **Executive Overview:** 4 KPI cards, AI tool popularity, average time saved by group, recommendation by satisfaction, 3 slicers and mean satisfaction.
2. **Usage & Productivity:** 3 KPI cards, respondent-level scatterplot, weekly time saved by tool, spending group vs satisfaction, and slicers.

## How to open

1. Extract the entire repository ZIP. Keep `.pbip`, `.Report`, `.SemanticModel` together.
2. Install a recent **Power BI Desktop** version on Windows. PBIR/PBIP compatibility varies by version; if asked to enable enhanced PBIR report format, use `File > Options and settings > Options > Preview features`.
3. Double-click **`powerbi/AI_Usage_Dashboard.pbip`** (not `definition.pbir`).
4. If prompted that model data needs loading, choose **Refresh** or **Apply changes**; loading the embedded Power Query import may take a moment. Then **File > Save As > Power BI Desktop file (.pbix)** if you want a single `.pbix` file.
5. Use the **User Type**, **AI Tool**, and **Country** slicers to filter visuals.

### If your version cannot open the project

Power BI Desktop is a Windows app, so this project was created from Microsoft's published PBIP/PBIR/TMDL source structure and validated for internal references, **but opening/rendering it in Desktop could not be tested in this environment**. If opening fails or a visual needs repairing, use the provided `DAX_MEASURES.md` and cleaned CSV to build the same pages in Power BI Desktop. The README includes the dashboard design reference.

#### Manual fallback

1. In Desktop: **Get data > Text/CSV** > select `data/processed/AI_Usage_Cleaned.csv` > Load.
2. In **Data** view, set hours, satisfaction, cost, and productivity columns to **Decimal number**.
3. Add **New columns**:

```DAX
Satisfaction_Band = IF(ISBLANK('AI Usage'[Satisfaction_Score]), BLANK(), SWITCH(TRUE(), 'AI Usage'[Satisfaction_Score] <= 5, "Low (<=5)", 'AI Usage'[Satisfaction_Score] <= 7, "Moderate (6-7)", "High (>=8)"))
AI_Cost_Group = IF(ISBLANK('AI Usage'[Monthly_AI_Cost]), BLANK(), IF('AI Usage'[Monthly_AI_Cost] = 0, "No reported cost", "Reported cost > 0"))
```

4. Add the measures in `DAX_MEASURES.md`. Change the import table name to `AI Usage` if necessary.
5. Recreate the visuals from `preview/dashboard_concept.png` and the **Pages** description above. Save as `.pbix`.

## Refresh / data lineage

The source of truth for this project remains `data/raw/...csv`. Run `python -m src.analysis` to regenerate the cleaned CSV. The `.pbip` intentionally contains a **snapshot** of cleaned data embedded in the M expression for portability; Power BI **Refresh** reloads that embedded snapshot, *not* a newer version of the external CSV. For new data, use the manual CSV connection workflow or regenerate the embedded payload.

## Methodology and limits

- Exact duplicates removed in Python, categories standardized, numeric-like text parsed, and missing values retained.
- All scores and savings are self-reported; relationships are descriptive rather than causal.
- Different answers have different valid sample sizes, and some observations are extreme.
- Monetary amounts may be in different undocumented currencies; do not interpret spending categories as cross-country price comparisons.
- `Recommend Yes Rate` uses all **non-missing** recommendation responses as denominator.
- Tool-level means can be unstable when few respondents use a tool; check sample sizes.
- Source, consent, and dataset redistribution permissions must be verified before publishing raw respondent records.

## Source-format references

- [Power BI Desktop Projects (Microsoft)](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [Power BI Desktop Report folder and PBIR](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- [Tabular Model Definition Language](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview)
