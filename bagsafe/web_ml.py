from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DEFAULT_DATASET = Path(r"C:\Users\saich\Downloads\baggage_master.json")


@dataclass(slots=True)
class WebPredictionResult:
    risk: str
    score: int
    probability: float
    reasons: list[str]
    recommendations: list[str]


@dataclass(slots=True)
class RouteFeatureMatch:
    values: dict[str, float]
    match_level: str


class WebRiskPredictor:
    def __init__(self, model_path: Path, dataset_path: Path | None = None) -> None:
        self.model_path = Path(model_path)
        self.dataset_path = Path(dataset_path) if dataset_path else DEFAULT_DATASET
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self._bundle: dict[str, object] | None = None

    def ensure_model(self) -> dict[str, object]:
        if self._bundle is not None:
            return self._bundle
        if self.model_path.exists():
            self._bundle = joblib.load(self.model_path)
            return self._bundle
        self._bundle = self._train_model()
        joblib.dump(self._bundle, self.model_path)
        return self._bundle

    def _load_dataset(self) -> pd.DataFrame:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Training dataset not found: {self.dataset_path}")

        with self.dataset_path.open("r", encoding="utf-8") as source:
            rows = json.load(source)

        frame = pd.DataFrame(rows)
        required_columns = {
            "is_delay",
            "Month",
            "DayOfWeek",
            "Reporting_Airline",
            "Origin",
            "Dest",
            "CRSDepTime",
            "Distance",
            "AirTime",
        }
        missing = required_columns - set(frame.columns)
        if missing:
            missing_columns = ", ".join(sorted(missing))
            raise ValueError(f"Dataset is missing required columns: {missing_columns}")

        for column in ["Month", "DayOfWeek", "CRSDepTime", "Distance", "AirTime", "is_delay"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

        frame = frame.dropna(subset=["is_delay", "Reporting_Airline", "Origin", "Dest"])
        frame["is_delay"] = frame["is_delay"].astype(int)
        frame["route_key"] = frame["Origin"].astype(str) + "-" + frame["Dest"].astype(str)
        frame["airline_route_key"] = (
            frame["Reporting_Airline"].astype(str) + "|" + frame["Origin"].astype(str) + "|" + frame["Dest"].astype(str)
        )
        return frame

    def _train_model(self) -> dict[str, object]:
        frame = self._load_dataset()
        feature_columns = [
            "Month",
            "DayOfWeek",
            "CRSDepTime",
            "Distance",
            "AirTime",
            "Reporting_Airline",
            "Origin",
            "Dest",
        ]
        numeric_features = ["Month", "DayOfWeek", "CRSDepTime", "Distance", "AirTime"]
        categorical_features = ["Reporting_Airline", "Origin", "Dest"]

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "num",
                    Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                    numeric_features,
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

        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=240,
                        max_depth=14,
                        min_samples_leaf=2,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )

        X_train, X_test, y_train, y_test = train_test_split(
            frame[feature_columns],
            frame["is_delay"],
            test_size=0.2,
            random_state=42,
            stratify=frame["is_delay"],
        )
        pipeline.fit(X_train, y_train)
        accuracy = float(pipeline.score(X_test, y_test))

        route_stats = self._build_route_stats(frame)
        metadata = {
            "feature_columns": feature_columns,
            "route_stats": route_stats,
            "defaults": {
                "Month": int(frame["Month"].median()),
                "DayOfWeek": int(frame["DayOfWeek"].median()),
                "CRSDepTime": int(frame["CRSDepTime"].median()),
                "Distance": int(frame["Distance"].median()),
                "AirTime": int(frame["AirTime"].median()),
                "Reporting_Airline": str(frame["Reporting_Airline"].mode().iat[0]),
            },
            "metrics": {
                "accuracy": round(accuracy, 4),
                "training_rows": int(len(frame)),
            },
        }
        return {"pipeline": pipeline, "metadata": metadata}

    def _build_route_stats(self, frame: pd.DataFrame) -> dict[str, dict[str, dict[str, float]]]:
        def summarize(grouped: pd.core.groupby.generic.DataFrameGroupBy) -> dict[str, dict[str, float]]:
            summary = grouped.agg(
                CRSDepTime=("CRSDepTime", "median"),
                Distance=("Distance", "median"),
                AirTime=("AirTime", "median"),
            )
            return {
                str(index): {
                    "CRSDepTime": float(row["CRSDepTime"]),
                    "Distance": float(row["Distance"]),
                    "AirTime": float(row["AirTime"]),
                }
                for index, row in summary.iterrows()
            }

        return {
            "airline_route": summarize(frame.groupby("airline_route_key")),
            "route": summarize(frame.groupby("route_key")),
        }

    def training_metrics(self) -> dict[str, object]:
        bundle = self.ensure_model()
        metadata = bundle["metadata"]
        return dict(metadata.get("metrics", {}))

    def predict(self, payload: dict[str, object]) -> WebPredictionResult:
        bundle = self.ensure_model()
        pipeline: Pipeline = bundle["pipeline"]  # type: ignore[assignment]
        metadata: dict[str, object] = bundle["metadata"]  # type: ignore[assignment]

        airline_code = self._extract_airline_code(str(payload.get("flightNumber", "")))
        route_match = self._lookup_route_features(
            airline_code=airline_code,
            origin=str(payload.get("origin", "")).upper(),
            destination=str(payload.get("destination", "")).upper(),
            metadata=metadata,
        )
        route_features = route_match.values

        now = datetime.now()
        feature_row = {
            "Month": int(now.month),
            "DayOfWeek": int(now.isoweekday()),
            "CRSDepTime": int(route_features["CRSDepTime"]),
            "Distance": int(route_features["Distance"]),
            "AirTime": int(route_features["AirTime"]),
            "Reporting_Airline": airline_code,
            "Origin": str(payload.get("origin", "")).upper(),
            "Dest": str(payload.get("destination", "")).upper(),
        }

        model_frame = pd.DataFrame([feature_row], columns=metadata["feature_columns"])
        delay_probability = float(pipeline.predict_proba(model_frame)[0][1])
        baggage_pressure = self._baggage_pressure(payload)
        final_probability = self._blend_probability(
            delay_probability=delay_probability,
            baggage_pressure=baggage_pressure,
            match_level=route_match.match_level,
        )
        score = int(round(final_probability * 100))

        risk = self._score_to_risk(score)

        reasons = self._build_reasons(
            payload,
            delay_probability,
            baggage_pressure,
            route_features,
            airline_code,
            route_match.match_level,
        )
        recommendations = {
            "Low": [
                "Proceed with standard baggage transfer workflow.",
                "Keep the bag in routine monitoring.",
                "No immediate escalation is required.",
            ],
            "Medium": [
                "Flag the bag for transfer desk monitoring.",
                "Alert the next handling point about the tighter connection.",
                "Keep this record visible until the transfer is confirmed.",
            ],
            "High": [
                "Escalate for manual supervision immediately.",
                "Coordinate with loading and transfer teams as a priority.",
                "Prepare a fallback handling plan before the connection window closes.",
            ],
        }[risk]

        return WebPredictionResult(
            risk=risk,
            score=score,
            probability=final_probability,
            reasons=reasons,
            recommendations=recommendations,
        )

    def _lookup_route_features(
        self,
        airline_code: str,
        origin: str,
        destination: str,
        metadata: dict[str, object],
    ) -> RouteFeatureMatch:
        route_stats = metadata["route_stats"]
        airline_route_key = f"{airline_code}|{origin}|{destination}"
        route_key = f"{origin}-{destination}"
        defaults = metadata["defaults"]

        airline_route = route_stats["airline_route"].get(airline_route_key)
        if airline_route:
            return RouteFeatureMatch(values=airline_route, match_level="airline_route")

        route_only = route_stats["route"].get(route_key)
        if route_only:
            return RouteFeatureMatch(values=route_only, match_level="route")

        return RouteFeatureMatch(
            values={
                "CRSDepTime": float(defaults["CRSDepTime"]),
                "Distance": float(defaults["Distance"]),
                "AirTime": float(defaults["AirTime"]),
            },
            match_level="default",
        )

    def _extract_airline_code(self, flight_number: str) -> str:
        match = re.match(r"([A-Za-z]{2,3})", flight_number.strip().upper())
        if match:
            return match.group(1)

        defaults = self.ensure_model()["metadata"]["defaults"]
        return str(defaults["Reporting_Airline"])

    def _baggage_pressure(self, payload: dict[str, object]) -> float:
        layover = max(int(payload.get("layoverMinutes", 0) or 0), 1)
        transfer_points = max(int(payload.get("transferPoints", 0) or 0), 1)
        terminal_distance = max(int(payload.get("terminalDistance", 0) or 0), 0)
        incoming_delay = max(int(payload.get("incomingDelay", 0) or 0), 0)
        checked_bags = max(int(payload.get("checkedBags", 0) or 0), 1)
        baggage_type = str(payload.get("baggageType", "transfer")).strip().lower()
        priority_status = bool(payload.get("priorityStatus"))
        international_transfer = bool(payload.get("internationalTransfer"))

        pressure = (
            0.34 * np.clip((70 - layover) / 45, 0, 1.3)
            + 0.22 * np.clip(incoming_delay / 55, 0, 1.4)
            + 0.14 * np.clip((terminal_distance - 800) / 1200, 0, 1.2)
            + 0.10 * np.clip((transfer_points - 1) / 2, 0, 1)
            + 0.07 * np.clip((checked_bags - 1) / 3, 0, 1)
            + 0.08 * int(international_transfer)
        )

        if baggage_type == "fragile":
            pressure += 0.06
        elif baggage_type == "transfer":
            pressure += 0.03

        if baggage_type == "priority" or priority_status:
            pressure -= 0.12

        return float(np.clip(pressure, 0.0, 1.0))

    def _blend_probability(self, delay_probability: float, baggage_pressure: float, match_level: str) -> float:
        model_weight = {
            "airline_route": 0.55,
            "route": 0.45,
            "default": 0.30,
        }.get(match_level, 0.40)
        pressure_weight = 1.0 - model_weight
        combined = delay_probability * model_weight + baggage_pressure * pressure_weight
        return float(np.clip(combined, 0.02, 0.98))

    def _score_to_risk(self, score: int) -> str:
        if score >= 68:
            return "High"
        if score >= 35:
            return "Medium"
        return "Low"

    def _build_reasons(
        self,
        payload: dict[str, object],
        delay_probability: float,
        baggage_pressure: float,
        route_features: dict[str, float],
        airline_code: str,
        match_level: str,
    ) -> list[str]:
        reasons: list[str] = []
        origin = str(payload.get("origin", "")).upper()
        destination = str(payload.get("destination", "")).upper()
        layover = int(payload.get("layoverMinutes", 0) or 0)
        incoming_delay = int(payload.get("incomingDelay", 0) or 0)
        terminal_distance = int(payload.get("terminalDistance", 0) or 0)
        transfer_points = int(payload.get("transferPoints", 0) or 0)
        baggage_type = str(payload.get("baggageType", "transfer")).strip().lower()
        priority_status = bool(payload.get("priorityStatus"))

        if delay_probability >= 0.6:
            reasons.append(
                f"Historical {airline_code} service on {origin}-{destination} shows elevated delay risk."
            )
        elif delay_probability >= 0.4:
            reasons.append(
                f"Historical flight patterns for {origin}-{destination} suggest moderate delay pressure."
            )
        else:
            reasons.append(
                f"Historical flight data for {origin}-{destination} is relatively stable for this route profile."
            )

        if match_level == "default":
            reasons.append(
                "This route is not in the saved history yet, so the score leans more on live transfer conditions."
            )

        if layover < 45:
            reasons.append("Short layover leaves very limited time for bag transfer.")
        elif layover < 75:
            reasons.append("Moderate layover still needs close baggage coordination.")

        if incoming_delay > 25:
            reasons.append("Incoming delay is already shrinking the available transfer window.")
        if terminal_distance > 1400:
            reasons.append("Long terminal distance increases handling pressure across the connection.")
        if transfer_points >= 3:
            reasons.append("Multiple transfer points add extra handoff risk.")
        if baggage_type == "fragile":
            reasons.append("Fragile baggage may move through a slower handling path.")
        if baggage_type == "priority" or priority_status:
            reasons.append("Priority handling helps reduce the chance of a missed transfer.")

        if len(reasons) == 1 and baggage_pressure >= 0.45:
            reasons.append(
                f"Estimated route distance of about {int(route_features['Distance'])} miles still adds operational complexity."
            )

        return reasons[:4]
