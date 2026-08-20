import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import TimeSeriesSplit
import os
import random

# Load JSON data
with open("../json/AQUASTAT_JSON/aquastat.json", "r") as file:
    data = json.load(file)

df = pd.DataFrame(data)

# Ensure correct data types
df["Year"] = df["Year"].astype(int)
df["Value"] = df["Value"].astype(float)

# Apply proportional noise
np.random.seed(42)  # For reproducibility, you can change the seed
df["Noise"] = np.random.uniform(0.01, 0.05, size=len(df)) * df["Value"]
df["Value"] += df["Noise"]

# Interpolate missing values by linear interpolation
df["Value"] = df["Value"].interpolate(method='linear')

# Years to predict
future_years = list(range(2022, 2031))

predictions = []

# The two next functions are used to correct the predicted values for invalid results
def correct_percentage(value, variable_name):
    """Function to correct predicted values for percentage variables. A pourcentage is between 0 and 100."""
    if isinstance(value, (int, float)):
        if "Agricultural water withdrawal as % of total renewable water resources" in variable_name or "SDG 6.4.2. Water Stress" in variable_name:
            if value <= 0: # Ensure it doesn't go below 0
                noise = random.uniform(0.1, 0.01)
                return max(value, 0) + noise
            elif value >= 100:
                noise = random.uniform(-0.1, -0.01)
                return (min(value, 100) + noise) # Ensure the result of noise + value doesn't go above 100
    return value


def correct_non_percentage(value, last_known_value,  min_value=1):
    """Function to prevent large drops in predicted values for non-percentage variables.
    If the predicted value drops too much from the last known value, adjust it."""
    if isinstance(value, (int, float)):
        if value < min_value:
            corrected_value = max(last_known_value * 0.95, min_value)  # Adjust it to 90% of last known value
            return corrected_value
    return value


for (iso3, variable), group in df.groupby(["ISO3", "Variable"]):
    group = group.sort_values("Year")

    # Check for NaN in 2018-2021, null values are skipped
    if group[(group["Year"].between(2018, 2021)) & (group["Value"].isna())].any().any():
        print(f"Skipping {iso3} due to NaN values in 2018-2021")
        continue

    # Train model only if we have at least 4 past years
    if len(group) < 4:
        continue

    X = group[["Year"]].values
    y = group["Value"].values

    # Time series cross-validation
    tscv = TimeSeriesSplit(n_splits=3)
    degrees = [1, 2, 3, 4]
    best_degree = None
    best_rmse = float('inf')

    # Polynomial regression
    for degree in degrees:
        rmses = []
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            model = make_pipeline(PolynomialFeatures(degree=degree), LinearRegression())
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            rmses.append(np.sqrt(mean_squared_error(y_test, y_pred)))

        avg_rmse = np.mean(rmses)
        if avg_rmse < best_rmse:
            best_rmse = avg_rmse
            best_degree = degree

    print(f"Best degree for {iso3} ({variable}): {best_degree}, RMSE: {best_rmse}")

    # Train
    final_model = make_pipeline(PolynomialFeatures(degree=best_degree), LinearRegression())
    final_model.fit(X, y)

    # Prediction
    for year in future_years:
        year_poly = final_model.named_steps['polynomialfeatures'].transform([[year]])
        pred_value = final_model.named_steps['linearregression'].predict(year_poly)[0]
        pred_value = correct_percentage(pred_value, variable)
        last_known_value = group[group["Year"] == group["Year"].max()]["Value"].values[0]
        pred_value = correct_non_percentage(pred_value, last_known_value)
        predictions.append({
            "ISO3": iso3,
            "Year": year,
            "Value": pred_value,
            "Variable": variable,
            "RMSE": best_rmse,
            "BestDegree": best_degree
        })

# Save predictions
output_path = "../json/AQUASTAT_JSON/aquastat_predictions.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as file:
    json.dump(predictions, file, indent=4)
print("Predictions saved to aquastat_predictions.json")
