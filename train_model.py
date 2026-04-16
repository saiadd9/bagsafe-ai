from pathlib import Path

from bagsafe.web_ml import DEFAULT_DATASET, WebRiskPredictor


def main() -> None:
    predictor = WebRiskPredictor(
        model_path=Path("artifacts") / "web_risk_model.joblib",
        dataset_path=DEFAULT_DATASET,
    )
    metrics = predictor.training_metrics()
    print(
        "Model trained from",
        DEFAULT_DATASET,
        f"with {metrics.get('training_rows', 0)} rows and accuracy {metrics.get('accuracy', 0):.4f}",
    )


if __name__ == "__main__":
    main()
