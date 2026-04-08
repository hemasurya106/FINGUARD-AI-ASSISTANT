import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Load data
df = pd.read_csv("expenses.csv")
df["date"] = pd.to_datetime(df["date"])

# Aggregate daily spending
daily = df.groupby("date").agg(
    total_spend=("amount", "sum"),
    food_spend=("amount", lambda x: x[df.loc[x.index, "category"] == "Food"].sum()),
    shopping_spend=("amount", lambda x: x[df.loc[x.index, "category"] == "Shopping"].sum())
).reset_index()

daily.fillna(0, inplace=True)

# Features for anomaly detection
X = daily[["total_spend", "food_spend", "shopping_spend"]]

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Isolation Forest
iso = IsolationForest(
    n_estimators=100,
    contamination=0.1,  # ~10% anomalies
    random_state=42
)

daily["anomaly"] = iso.fit_predict(X_scaled)

# -1 = anomaly, 1 = normal
anomalies = daily[daily["anomaly"] == -1]
daily[["date", "anomaly"]].to_csv("anomaly_days.csv", index=False)

print("🚨 Detected Anomalous Days:")
print(anomalies[["date", "total_spend", "food_spend", "shopping_spend"]])
print(f"\nTotal anomalies detected: {len(anomalies)}")
