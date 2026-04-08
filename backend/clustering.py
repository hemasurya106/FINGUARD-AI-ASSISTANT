import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Load data
df = pd.read_csv("expenses.csv")
df["date"] = pd.to_datetime(df["date"])

# Create daily aggregated features
daily = df.groupby("date").agg(
    total_spend=("amount", "sum"),
    food_spend=("amount", lambda x: x[df.loc[x.index, "category"] == "Food"].sum()),
    shopping_spend=("amount", lambda x: x[df.loc[x.index, "category"] == "Shopping"].sum()),
    weekend=("day_type", lambda x: 1 if x.iloc[0] == "Weekend" else 0)
).reset_index()

# Replace NaN with 0
daily.fillna(0, inplace=True)

# Feature matrix
X = daily[["total_spend", "food_spend", "shopping_spend", "weekend"]]

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# K-Means clustering
kmeans = KMeans(n_clusters=2, random_state=42)
daily["cluster"] = kmeans.fit_predict(X_scaled)
daily.to_csv("clustered_days.csv", index=False)

print("✅ Daily behavior clustering result:")
print(daily.head())
print("\nCluster distribution:")
print(daily["cluster"].value_counts())
