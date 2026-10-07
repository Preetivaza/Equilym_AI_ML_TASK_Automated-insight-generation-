"""Headless run: writes sample outputs (insights.csv/json, correlation_matrix.csv)."""
import engine as E
df = E.load_data("data/district_data.csv")
rep = E.validation_report(df)
print(rep["head"]); print(rep["info"]); print(rep["missing"])
ins, corr = E.generate_insights(df)
ins.to_csv("outputs/insights.csv", index=False)
ins.to_json("outputs/insights.json", orient="records", indent=2)
corr.to_csv("outputs/correlation_matrix.csv")
print(ins[["insight_id", "type", "entity", "indicator", "severity"]])
