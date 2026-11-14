"""Machine Learning part: Random Forest predicts the CHANCE of load shedding.

Inputs  (features): area, weekday, temperature
Output  (target)  : load shedding on that day? (Yes / No)  ->  chance in %

The timing (off / on) of each area is fixed and comes from area_timings.csv.
The model only decides how likely it is that load shedding happens.
"""

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from logic import estimated_temperature

BASE_DIR = Path(__file__).parent
HISTORY_FILE = BASE_DIR / "data" / "history.csv"
FEATURES = ["area", "weekday", "temperature"]


class LoadSheddingModel:
    def __init__(self, history_file=HISTORY_FILE):
        self.history_file = history_file
        self.pipeline = None
        self.accuracy = None
        self.rows = 0

    def train(self):
        df = pd.read_csv(self.history_file)
        df = df.dropna(subset=["Area", "Date", "Temperature", "Load Shedding"])
        df = df.drop_duplicates()

        data = pd.DataFrame({
            "area": df["Area"],
            "weekday": pd.to_datetime(df["Date"]).dt.weekday,   # Monday=0 ... Sunday=6
            "temperature": df["Temperature"],
        })
        target = (df["Load Shedding"] == "Yes").astype(int)

        X_train, X_test, y_train, y_test = train_test_split(
            data[FEATURES], target, test_size=0.2, random_state=42, stratify=target
        )

        preprocess = ColumnTransformer(
            [("area", OneHotEncoder(handle_unknown="ignore"), ["area"])],
            remainder="passthrough",
        )
        self.pipeline = Pipeline([
            ("prepare", preprocess),
            ("forest", RandomForestClassifier(
                n_estimators=150, min_samples_leaf=8, random_state=42)),
        ])
        self.pipeline.fit(X_train, y_train)

        self.accuracy = accuracy_score(y_test, self.pipeline.predict(X_test))
        self.rows = len(df)
        return self.accuracy

    def chance(self, area, day):
        """Chance (0-100 %) that load shedding happens in `area` on date `day`."""
        row = pd.DataFrame([{
            "area": area,
            "weekday": day.weekday(),
            "temperature": estimated_temperature(day),
        }])
        probabilities = self.pipeline.predict_proba(row[FEATURES])[0]
        yes_index = list(self.pipeline.classes_).index(1)
        return float(probabilities[yes_index]) * 100
