import pandas as pd

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load clustering output
cluster_df = pd.read_csv(os.path.join(BASE_DIR, "clustered_days.csv"))  
# Expected columns: date, total_spend, cluster

# Load anomaly output
anomaly_df = pd.read_csv(os.path.join(BASE_DIR, "anomaly_days.csv"))  
# Expected columns: date, anomaly

# Merge both
df = pd.merge(cluster_df, anomaly_df, on="date", how="inner")

def generate_recommendation(row):
    if row["cluster"] == 1 and row["anomaly"] == -1:
        return "⚠ High-risk spending detected. Consider delaying non-essential purchases."
    elif row["cluster"] == 1:
        return "High spending day. Monitor your expenses carefully."
    elif row["anomaly"] == -1:
        return "Unusual spending pattern detected. Review today’s expenses."
    else:
        return "Spending is within your normal range."

df["recommendation"] = df.apply(generate_recommendation, axis=1)

print("🧠 Daily Recommendations:")
print(df[["date", "total_spend", "recommendation"]])

df.to_csv(os.path.join(BASE_DIR, "recommendations.csv"), index=False)
print("✅ Recommendations saved to recommendations.csv")
