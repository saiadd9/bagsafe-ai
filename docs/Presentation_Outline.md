# Presentation Outline

## Slide 1: Title

- Project name: `BagSafe AI`
- Student names and IDs
- Course: Advanced Python Application Development

## Slide 2: Problem Statement

- Baggage transfer failures create delays, costs, and poor passenger experience.
- Airport staff need an early warning tool for risky transfers.

## Slide 3: Proposed Solution

- Desktop application for entering baggage transfer details.
- Predicts `Low`, `Medium`, or `High` transfer risk.
- Stores records for follow-up tracking.

## Slide 4: CLO Achievement

- `CLO 1`: OOP classes for core entities.
- `CLO 2`: Inheritance and overriding in baggage subclasses.
- `CLO 3`: Separation of GUI, ML, and database concerns.
- `CLO 6`: Tkinter GUI with forms, outputs, and record table.

## Slide 5: System Design

- Show the UML/class diagram from the SDD.
- Explain why abstraction and encapsulation improve maintainability.

## Slide 6: Machine Learning

- Features used: layover, delay, transfer points, terminal distance, bag count, bag type, priority, transfer type.
- Model used: `RandomForestClassifier`.
- Explain that the baggage-risk training data is generated from operational flight patterns because direct baggage-failure labels were unavailable.

## Slide 7: GUI Demonstration

- Show data entry form.
- Run a prediction.
- Explain confidence score and recommendation.

## Slide 8: Database Demonstration

- Save a record.
- Search for a record.
- Delete a record.

## Slide 9: Challenges and Improvements

- Challenge: source data did not include baggage-level labels.
- Solution: engineer a realistic training dataset informed by flight-delay data.
- Future work: export reports, edit records, retrain with real baggage operations data.

## Slide 10: Conclusion

- Summarize project value.
- Reconfirm the CLOs achieved.
- Invite questions.

