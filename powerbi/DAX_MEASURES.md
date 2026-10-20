# Power BI measures (DAX)

These measures are already included in the `.SemanticModel/definition/tables/AI Usage.tmdl` file.
If Power BI Desktop cannot open the text-based project, import `data/processed/AI_Usage_Cleaned.csv` manually and create these measures in **Modeling > New measure**.

### Respondents

```DAX
Respondents = DISTINCTCOUNT('AI Usage'[User_ID])
```

### Average Daily AI Hours

```DAX
Average Daily AI Hours = AVERAGE('AI Usage'[AI_Usage_Hours_Per_Day])
```

### Average Weekly Time Saved

```DAX
Average Weekly Time Saved = AVERAGE('AI Usage'[Time_Saved_Hours_Per_Week])
```

### Average Productivity Score

```DAX
Average Productivity Score = AVERAGE('AI Usage'[Productivity_Score])
```

### Average Satisfaction Score

```DAX
Average Satisfaction Score = AVERAGE('AI Usage'[Satisfaction_Score])
```

### Total Recommendations Yes

```DAX
Total Recommendations Yes = CALCULATE(COUNTROWS('AI Usage'), 'AI Usage'[Would_Recommend] = "Yes")
```

### Valid Recommendation Responses

```DAX
Valid Recommendation Responses = CALCULATE(COUNTROWS('AI Usage'), NOT ISBLANK('AI Usage'[Would_Recommend]))
```

### Recommend Yes Rate

```DAX
Recommend Yes Rate = DIVIDE([Total Recommendations Yes], [Valid Recommendation Responses])
```

### Recorded Tool Users

```DAX
Recorded Tool Users = CALCULATE(COUNTROWS('AI Usage'), NOT ISBLANK('AI Usage'[AI_Tool]))
```

### Usage Hours per Respondent

```DAX
Usage Hours per Respondent = MAX('AI Usage'[AI_Usage_Hours_Per_Day])
```

### Productivity per Respondent

```DAX
Productivity per Respondent = MAX('AI Usage'[Productivity_Score])
```

### Valid Time Savings Responses

```DAX
Valid Time Savings Responses = COUNT('AI Usage'[Time_Saved_Hours_Per_Week])
```

