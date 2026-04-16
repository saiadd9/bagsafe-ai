# Technical Documentation

## Technologies Used

- `Python`: core programming language
- `Tkinter`: desktop GUI
- `SQLite`: local database storage
- `pandas` and `numpy`: feature preparation and synthetic dataset generation
- `scikit-learn`: machine learning pipeline and classifier
- `joblib`: model persistence

## Environment Setup

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```

Runtime artifacts are stored in the local `artifacts` folder. The SQLite connection uses memory-based journaling so it behaves more reliably in cloud-synced folders such as OneDrive.

## Code Structure

- `bagsafe/models.py`: encapsulates entities and OOP behavior.
- `bagsafe/database.py`: isolates SQL logic from UI logic.
- `bagsafe/ml.py`: handles training, preprocessing, persistence, and prediction.
- `bagsafe/gui.py`: manages event-driven GUI interactions.

## Machine Learning Approach

- The source dataset referenced in the proposal does not contain baggage-level failure labels.
- To keep the application feasible, the model uses a baggage-risk training frame generated from operational delay and distance patterns.
- If `all datasets.zip` is available, the generator samples real flight delay and distance distributions from `flight_data_2024_sample.csv`.
- The final model is a `RandomForestClassifier` predicting `Low`, `Medium`, or `High` transfer risk.

## Maintenance and Extension

- Add update/edit functionality by extending `DatabaseManager`.
- Replace the synthetic-label generator with a real baggage operations dataset if one becomes available.
- Export records to CSV or PDF for reporting.
- Add model evaluation metrics and a retraining utility for future versions.
