"""Run with: python -m unittest discover -s tests -v"""
import unittest

import pandas as pd

from src.analysis import (
    EXPECTED_COLUMNS,
    _parse_numeric,
    clean_data,
    read_raw_data,
    recommendation_summary,
)


class CleaningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = read_raw_data()
        cls.clean = clean_data(cls.raw)

    def test_original_dataset_kept_and_duplicates_removed(self):
        self.assertEqual(self.raw.shape, (300, 19))
        self.assertEqual(self.raw.duplicated().sum(), 12)
        self.assertEqual(self.clean.shape, (288, 19))
        self.assertEqual(self.clean["User_ID"].nunique(), 288)
        self.assertEqual(list(self.clean.columns), EXPECTED_COLUMNS)

    def test_variant_ai_tool_names_standardized(self):
        self.assertEqual(int(self.clean["AI_Tool"].eq("ChatGPT").sum()), 119)
        self.assertFalse(self.clean["AI_Tool"].isin(["Chat GPT", "chatgpt", "Chatgpt"]).any())

    def test_missing_measurements_not_imputed_as_zero(self):
        self.assertTrue(self.clean["Age"].isna().any())
        self.assertTrue(self.clean["Monthly_AI_Cost"].isna().any())

    def test_numeric_parsing(self):
        values = pd.Series(["2 hrs", "$20", "28 yrs", "1.5", None, "unknown"])
        actual = _parse_numeric(values)
        self.assertEqual(actual.iloc[:4].tolist(), [2, 20, 28, 1.5])
        self.assertTrue(pd.isna(actual.iloc[4]))
        self.assertTrue(pd.isna(actual.iloc[5]))

    def test_outliers_preserved_for_review(self):
        self.assertGreaterEqual(self.clean["Age"].max(), 97)
        self.assertGreaterEqual(self.clean["Monthly_Income"].max(), 250000)
        self.assertGreaterEqual(self.clean["AI_Usage_Hours_Per_Day"].max(), 23)

    def test_recommendation_rates_in_valid_range(self):
        summary = recommendation_summary(self.clean)
        self.assertEqual(len(summary), 3)
        self.assertTrue(summary["Yes_Rate"].between(0, 100).all())
        valid_pairs = self.clean[["Satisfaction_Score", "Would_Recommend"]].dropna()
        self.assertEqual(int(summary["Valid_Responses"].sum()), len(valid_pairs))


if __name__ == "__main__":
    unittest.main()
