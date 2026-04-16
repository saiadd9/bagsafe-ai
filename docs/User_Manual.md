# User Manual

## Starting the Application

1. Install the dependencies from `requirements.txt`.
2. Run `python main.py`.
3. Wait for the main BagSafe AI window to open.

## Making a Prediction

1. Enter the passenger, flight, and baggage details in the form.
2. Choose the baggage type and check the relevant transfer options.
3. Select `Predict and Save`.
4. Read the risk category, confidence score, and recommendation from the summary panel.

## Viewing and Managing Records

1. Saved records appear in the bottom table.
2. Use the search field to filter records.
3. Select a row and choose `Delete Selected` if a record should be removed.

## Troubleshooting

- If the app does not start, verify that required libraries were installed.
- If prediction fails, check that all numeric fields contain numbers.
- If the first launch is slow, the model may still be training and saving.

