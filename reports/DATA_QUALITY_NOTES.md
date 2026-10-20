# Data quality assessment and cleaning decisions

The project uses the supplied `AI_Usage_and_Impact_on_Students_and_Professionals.csv`. No independently verified information about its origin, collection method, data dictionary, or licensing was available.

## Dataset audit

| Check | Finding | Handling |
|---|---|---|
| Original dimensions | 300 rows × 19 columns | Preserve raw file unchanged |
| Exact duplicate records | 12 | Drop exact duplicates, leaving 288 rows |
| User identifiers | 288 unique IDs after deduplication | Keep anonymized identifiers; do not deduplicate by a different key |
| Missing observations | E.g., 23 raw ages, 11 raw AI tool names | Keep missing entries as missing; list counts in `data_quality_report.csv` |
| AI-tool aliases | `ChatGPT`, `Chat GPT`, `chatgpt`, `Chatgpt` | Standardize to `ChatGPT` (119 valid responses after deduplication) |
| Other labels | Mixed spellings/capitalization for gender, country, education | Standardize known aliases; avoid guessing unknown values |
| Numeric stored as text | Examples: `2 hrs`, `$20`, `28 yrs` | Parse known units/currency punctuation with safe numeric conversion |
| Unusual observations | Two ages of 97, income of 250,000, AI use of 23 hours/day | Flag for review and keep unless original source confirms an error |

## Explicit choices

1. **No blanket imputation:** Missing measurements are not equivalent to zero, so mean and correlation calculations use the available observations. Sample sizes accompany results.
2. **No automatic outlier removal:** There is no original survey documentation proving those observations are incorrect. An additional correlation is reported after excluding >16 AI-use hours/day *only from that sensitivity analysis*.
3. **Category mapping is explicit:** See `TOOL_ALIASES` and `EDUCATION_ALIASES` in `src/analysis.py` for mappings instead of opaque replacements.
4. **Spending comparison separates unknown from zero:** Blank AI cost values are not included in either spending group.
5. **Recommendation bands are analytic choices:** Low (≤5), moderate (6–7), and high (≥8) satisfaction bands were selected for the visual analysis; their interpretation is not claimed to be an official survey scoring standard.
6. **No causal conclusions:** Relationships can be confounded by user characteristics, use cases, and survey selection.

## Rebuild outputs

From repository root:

```bash
python -m src.analysis
```

This generates `data/processed/AI_Usage_Cleaned.csv`, `reports/data_quality_report.csv`, and six charts under `reports/figures/`. `python -m unittest discover -s tests -v` verifies key data transformations.
