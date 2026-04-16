# BagSafe AI

BagSafe AI is a Python desktop application for predicting baggage transfer failure risk in airport operations. It demonstrates object-oriented design, inheritance and overriding, encapsulation, abstraction, SQLite CRUD operations, and a Tkinter GUI.

## Features

- Predicts `Low`, `Medium`, or `High` baggage transfer risk.
- Stores assessment records in SQLite and lists them in the GUI.
- Uses OOP classes for passengers, flights, routes, and specialized baggage types.
- Trains a `RandomForestClassifier` and reuses the saved model on later runs.
- Supports search and delete operations for stored records.

## Project Structure

- `main.py`: application entry point
- `bagsafe/models.py`: domain classes and inheritance hierarchy
- `bagsafe/database.py`: SQLite database layer
- `bagsafe/ml.py`: training and prediction pipeline
- `bagsafe/gui.py`: Tkinter interface
- `docs/`: software documentation, technical notes, and user manual

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python main.py
```

## Notes

- The first launch trains a model and saves it in `artifacts/bagsafe_model.joblib`.
- Records are stored in `artifacts/bagsafe_runtime.db`.
- SQLite uses memory-based journaling so the database works more reliably in cloud-synced folders.
- If the provided `all datasets.zip` is available in the original download path, the training generator uses its flight delay profile to make the synthetic baggage-risk training set more realistic.
