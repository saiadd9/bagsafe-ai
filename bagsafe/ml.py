from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass(slots=True)
class PredictionOutcome:
    category: str
    probability: float
    recommendation: str


class PredictionModel:
    def __init__(self, model_path: Path, source_zip: Path | None = None) -> None:
        self.model_path = Path(model_path)
        self.source_zip = Path(source_zip) if source_zip else None
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self._model: Pipeline | None = None

    def ensure_model(self) -> Pipeline:
        if self._model is not None:
            return self._model
        if self.model_path.exists():
            self._model = joblib.load(self.model_path)
            return self._model
        self._model = self._train_model()
        joblib.dump(self._model, self.model_path)
        return self._model

    def _train_model(self) -> Pipeline:
        frame = self._build_training_frame()
        feature_columns = [
            "layover_minutes",
            "transfer_points",
            "terminal_distance_meters",
            "incoming_delay_minutes",
            "checked_bags",
            "priority_status",
            "international_transfer",
            "baggage_type",
        ]
        numeric_features = [
            "layover_minutes",
            "transfer_points",
            "terminal_distance_meters",
            "incoming_delay_minutes",
            "checked_bags",
        ]
        binary_features = ["priority_status", "international_transfer"]
        categorical_features = ["baggage_type"]

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "num",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    numeric_features,
                ),
                (
                    "bin",
                    Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent"))]),
                    binary_features,
                ),
                (
                    "cat",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            ("encoder", OneHotEncoder(handle_unknown="ignore")),
                        ]
                    ),
                    categorical_features,
                ),
            ]
        )

        model = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=220,
                        max_depth=10,
                        random_state=42,
                        class_weight="balanced",
                    ),
                ),
            ]
        )
        model.fit(frame[feature_columns], frame["risk_category"])
        return model

    def _load_delay_profile(self) -> tuple[np.ndarray, np.ndarray]:
        if not self.source_zip or not self.source_zip.exists():
            return (
                np.array([-8, -2, 3, 8, 15, 28, 45, 60], dtype=float),
                np.array([280, 500, 800, 1100, 1600, 2100], dtype=float),
            )

        try:
            with ZipFile(self.source_zip) as archive:
                with archive.open("file/flight_data_2024_sample.csv") as source:
                    frame = pd.read_csv(source, usecols=["dep_delay", "distance"])
            delay = frame["dep_delay"].fillna(frame["dep_delay"].median()).to_numpy(dtype=float)
            distance = frame["distance"].fillna(frame["distance"].median()).to_numpy(dtype=float)
            return delay, distance
        except Exception:
            return (
                np.array([-8, -2, 3, 8, 15, 28, 45, 60], dtype=float),
                np.array([280, 500, 800, 1100, 1600, 2100], dtype=float),
            )

    def _build_training_frame(self, size: int = 1800) -> pd.DataFrame:
        rng = np.random.default_rng(42)
        delays, distances = self._load_delay_profile()
        bag_types = np.array(["transfer", "fragile", "priority"], dtype=object)

        incoming_delay = np.clip(rng.choice(delays, size=size, replace=True) + rng.normal(0, 6, size), -20, 120)
        terminal_distance = np.clip(
            rng.choice(distances, size=size, replace=True) * rng.uniform(0.55, 1.1, size),
            150,
            2600,
        )
        layover_minutes = np.clip(
            rng.normal(82, 28, size=size) - incoming_delay * 0.18 + rng.normal(0, 6, size=size),
            25,
            220,
        )
        transfer_points = rng.choice([1, 2, 3], size=size, p=[0.58, 0.3, 0.12])
        checked_bags = rng.choice([1, 2, 3, 4], size=size, p=[0.52, 0.3, 0.14, 0.04])
        international_transfer = rng.choice([0, 1], size=size, p=[0.78, 0.22])
        priority_status = rng.choice([0, 1], size=size, p=[0.76, 0.24])
        baggage_type = rng.choice(bag_types, size=size, p=[0.62, 0.2, 0.18])

        bag_modifier = np.select(
            [baggage_type == "priority", baggage_type == "fragile"],
            [-0.08, 0.07],
            default=0.12,
        )

        risk_score = (
            0.36 * np.clip((65 - layover_minutes) / 40, 0, 1.5)
            + 0.24 * np.clip(incoming_delay / 60, 0, 2)
            + 0.16 * np.clip((terminal_distance - 750) / 1200, 0, 1.6)
            + 0.11 * np.clip((transfer_points - 1) / 2, 0, 1)
            + 0.06 * np.clip((checked_bags - 1) / 3, 0, 1)
            + 0.07 * international_transfer
            + bag_modifier
            - 0.09 * priority_status
            + rng.normal(0, 0.045, size=size)
        )

        categories = np.where(risk_score >= 0.6, "High", np.where(risk_score >= 0.33, "Medium", "Low"))
        return pd.DataFrame(
            {
                "layover_minutes": layover_minutes.round().astype(int),
                "transfer_points": transfer_points.astype(int),
                "terminal_distance_meters": terminal_distance.round().astype(int),
                "incoming_delay_minutes": incoming_delay.round().astype(int),
                "checked_bags": checked_bags.astype(int),
                "priority_status": priority_status.astype(int),
                "international_transfer": international_transfer.astype(int),
                "baggage_type": baggage_type,
                "risk_category": categories,
            }
        )

    def predict(self, features: dict[str, object], type_modifier: float = 0.0) -> PredictionOutcome:
        model = self.ensure_model()
        frame = pd.DataFrame([features])
        probabilities = model.predict_proba(frame)[0]
        indexed = dict(zip(model.classes_, probabilities, strict=True))

        high = indexed.get("High", 0.0)
        medium = indexed.get("Medium", 0.0)
        adjusted_high = min(max(high + max(type_modifier, 0) * 0.2, 0), 1)
        adjusted_medium = min(max(medium + type_modifier * 0.05, 0), 1)

        if adjusted_high >= 0.5:
            category = "High"
            probability = adjusted_high
        elif adjusted_high + adjusted_medium >= 0.55:
            category = "Medium"
            probability = max(adjusted_medium, adjusted_high + adjusted_medium)
        else:
            category = "Low"
            probability = indexed.get("Low", 0.0)

        recommendation = {
            "Low": "Proceed with standard transfer handling.",
            "Medium": "Flag this bag for transfer desk monitoring.",
            "High": "Escalate to priority transfer and manual supervision.",
        }[category]
        return PredictionOutcome(category=category, probability=float(probability), recommendation=recommendation)

