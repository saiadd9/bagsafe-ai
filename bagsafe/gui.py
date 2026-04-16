from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from bagsafe.database import DatabaseManager
from bagsafe.ml import PredictionModel
from bagsafe.models import BaggageAssessment, FlightSegment, Passenger, TransferRoute, build_baggage


ROOT_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
DEFAULT_ZIP = Path(r"C:\Users\jahnv.DIVYA-RAGESH\Downloads\Dataset - Project\all datasets.zip")


class BagSafeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BagSafe AI")
        self.geometry("1240x760")
        self.minsize(1180, 700)
        self.configure(bg="#eef3f8")

        self.database = DatabaseManager(ARTIFACTS_DIR / "bagsafe_runtime.db")
        self.model = PredictionModel(
            ARTIFACTS_DIR / "bagsafe_model.joblib",
            DEFAULT_ZIP if DEFAULT_ZIP.exists() else None,
        )

        self.prediction_value = tk.StringVar(value="No prediction yet")
        self.score_value = tk.StringVar(value="0.00")
        self.recommendation_value = tk.StringVar(value="Run a prediction to get an operational recommendation.")
        self.search_var = tk.StringVar()
        self.fields: dict[str, tk.Variable] = {}

        self._build_styles()
        self._build_layout()
        self.refresh_records()

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Card.TFrame", background="white")
        style.configure("Header.TLabel", background="white", foreground="#12324a", font=("Calibri", 17, "bold"))
        style.configure("Sub.TLabel", background="white", foreground="#4d6678", font=("Calibri", 10))
        style.configure("Result.TLabel", background="#12324a", foreground="white", font=("Calibri", 13, "bold"))
        style.configure("Treeview", rowheight=28, font=("Calibri", 10))
        style.configure("Treeview.Heading", font=("Calibri", 10, "bold"))

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(2, weight=1)

        header = ttk.Frame(container, style="Card.TFrame", padding=18)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        ttk.Label(header, text="BagSafe AI", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Predict baggage transfer failure risk using OOP design, SQLite storage, and a scikit-learn model.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        form_card = ttk.Frame(container, style="Card.TFrame", padding=18)
        form_card.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        form_card.columnconfigure(0, weight=1)
        form_card.columnconfigure(1, weight=1)

        result_card = ttk.Frame(container, style="Card.TFrame", padding=18)
        result_card.grid(row=1, column=1, sticky="nsew")
        result_card.columnconfigure(0, weight=1)

        table_card = ttk.Frame(container, style="Card.TFrame", padding=18)
        table_card.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(16, 0))
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(1, weight=1)

        self._build_form(form_card)
        self._build_results(result_card)
        self._build_table(table_card)

    def _build_form(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Transfer Assessment Form", style="Header.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )

        field_specs = [
            ("Passenger Name", "passenger_name", tk.StringVar(value="Aisha Rahman")),
            ("Booking Ref", "booking_reference", tk.StringVar(value="BRG472")),
            ("Bag Tag", "tag_number", tk.StringVar(value="BG-1001")),
            ("Flight Number", "flight_number", tk.StringVar(value="EK211")),
            ("Origin", "origin", tk.StringVar(value="DXB")),
            ("Destination", "destination", tk.StringVar(value="LHR")),
            ("Layover (min)", "layover_minutes", tk.StringVar(value="55")),
            ("Transfer Points", "transfer_points", tk.StringVar(value="2")),
            ("Terminal Distance (m)", "terminal_distance_meters", tk.StringVar(value="1200")),
            ("Incoming Delay (min)", "incoming_delay_minutes", tk.StringVar(value="18")),
            ("Checked Bags", "checked_bags", tk.StringVar(value="2")),
        ]

        for index, (label, key, variable) in enumerate(field_specs, start=1):
            column = (index - 1) % 2
            row = ((index - 1) // 2) * 2 + 1
            self.fields[key] = variable
            ttk.Label(parent, text=label, style="Sub.TLabel").grid(
                row=row, column=column, sticky="w", pady=(10, 2), padx=(0, 10)
            )
            ttk.Entry(parent, textvariable=variable, font=("Calibri", 11)).grid(
                row=row + 1, column=column, sticky="ew", padx=(0, 10)
            )

        self.fields["baggage_type"] = tk.StringVar(value="transfer")
        self.fields["priority_status"] = tk.BooleanVar(value=False)
        self.fields["international_transfer"] = tk.BooleanVar(value=True)

        extra_row = 13
        ttk.Label(parent, text="Baggage Type", style="Sub.TLabel").grid(row=extra_row, column=0, sticky="w", pady=(10, 2))
        ttk.Combobox(
            parent,
            textvariable=self.fields["baggage_type"],
            values=["transfer", "fragile", "priority"],
            state="readonly",
            font=("Calibri", 11),
        ).grid(row=extra_row + 1, column=0, sticky="ew", padx=(0, 10))

        ttk.Checkbutton(parent, text="Priority Status", variable=self.fields["priority_status"]).grid(
            row=extra_row + 1, column=1, sticky="w"
        )
        ttk.Checkbutton(parent, text="International Transfer", variable=self.fields["international_transfer"]).grid(
            row=extra_row + 2, column=1, sticky="w", pady=(6, 0)
        )

        button_bar = ttk.Frame(parent, style="Card.TFrame")
        button_bar.grid(row=extra_row + 3, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        ttk.Button(button_bar, text="Predict and Save", command=self.predict_and_save).pack(side="left", padx=(0, 8))
        ttk.Button(button_bar, text="Refresh Records", command=self.refresh_records).pack(side="left", padx=(0, 8))
        ttk.Button(button_bar, text="Clear Form", command=self.clear_form).pack(side="left")

    def _build_results(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Prediction Summary", style="Header.TLabel").grid(row=0, column=0, sticky="w")

        score_panel = tk.Frame(parent, bg="#12324a", padx=18, pady=18)
        score_panel.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(score_panel, text="Risk Category", style="Result.TLabel").pack(anchor="w")
        tk.Label(score_panel, textvariable=self.prediction_value, bg="#12324a", fg="white", font=("Calibri", 24, "bold")).pack(anchor="w")
        tk.Label(score_panel, text="Confidence", bg="#12324a", fg="#b8d0de", font=("Calibri", 11)).pack(anchor="w", pady=(12, 0))
        tk.Label(score_panel, textvariable=self.score_value, bg="#12324a", fg="white", font=("Calibri", 17, "bold")).pack(anchor="w")

        ttk.Label(parent, text="Operational Recommendation", style="Sub.TLabel").grid(row=2, column=0, sticky="w", pady=(18, 4))
        ttk.Label(parent, textvariable=self.recommendation_value, wraplength=330, style="Sub.TLabel").grid(row=3, column=0, sticky="w")

    def _build_table(self, parent: ttk.Frame) -> None:
        top_bar = ttk.Frame(parent, style="Card.TFrame")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top_bar.columnconfigure(1, weight=1)

        ttk.Label(top_bar, text="Stored Records", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(top_bar, textvariable=self.search_var, font=("Calibri", 11)).grid(row=0, column=1, sticky="ew", padx=12)
        ttk.Button(top_bar, text="Search", command=self.refresh_records).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(top_bar, text="Delete Selected", command=self.delete_selected).grid(row=0, column=3)

        columns = ("id", "passenger", "tag", "flight", "route", "type", "risk", "score", "created")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        headings = {
            "id": "ID",
            "passenger": "Passenger",
            "tag": "Bag Tag",
            "flight": "Flight",
            "route": "Route",
            "type": "Type",
            "risk": "Risk",
            "score": "Score",
            "created": "Created",
        }
        widths = {"id": 50, "passenger": 170, "tag": 100, "flight": 100, "route": 110, "type": 90, "risk": 80, "score": 80, "created": 120}
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center")

        self.tree.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _validated_payload(self) -> dict[str, object]:
        try:
            payload = {
                "passenger_name": self.fields["passenger_name"].get().strip(),
                "booking_reference": self.fields["booking_reference"].get().strip().upper(),
                "tag_number": self.fields["tag_number"].get().strip().upper(),
                "flight_number": self.fields["flight_number"].get().strip().upper(),
                "origin": self.fields["origin"].get().strip().upper(),
                "destination": self.fields["destination"].get().strip().upper(),
                "layover_minutes": int(self.fields["layover_minutes"].get()),
                "transfer_points": int(self.fields["transfer_points"].get()),
                "terminal_distance_meters": int(self.fields["terminal_distance_meters"].get()),
                "incoming_delay_minutes": int(self.fields["incoming_delay_minutes"].get()),
                "checked_bags": int(self.fields["checked_bags"].get()),
                "baggage_type": self.fields["baggage_type"].get(),
                "priority_status": bool(self.fields["priority_status"].get()),
                "international_transfer": bool(self.fields["international_transfer"].get()),
            }
        except ValueError as exc:
            raise ValueError("Numeric fields must contain valid whole numbers.") from exc

        required = ("passenger_name", "booking_reference", "tag_number", "flight_number", "origin", "destination")
        if any(not payload[key] for key in required):
            raise ValueError("Please complete all text fields before saving.")
        if payload["layover_minutes"] <= 0 or payload["checked_bags"] <= 0:
            raise ValueError("Layover and checked bag count must be greater than zero.")
        return payload

    def predict_and_save(self) -> None:
        try:
            payload = self._validated_payload()
            baggage = build_baggage(
                tag_number=str(payload["tag_number"]),
                baggage_type=str(payload["baggage_type"]),
                checked_bags=int(payload["checked_bags"]),
                priority_status=bool(payload["priority_status"]),
            )
            passenger = Passenger(full_name=str(payload["passenger_name"]), booking_reference=str(payload["booking_reference"]))
            flight = FlightSegment(
                flight_number=str(payload["flight_number"]),
                origin=str(payload["origin"]),
                destination=str(payload["destination"]),
            )
            route = TransferRoute(
                layover_minutes=int(payload["layover_minutes"]),
                transfer_points=int(payload["transfer_points"]),
                terminal_distance_meters=int(payload["terminal_distance_meters"]),
                incoming_delay_minutes=int(payload["incoming_delay_minutes"]),
                international_transfer=bool(payload["international_transfer"]),
            )

            features = route.as_features() | baggage.as_features()
            outcome = self.model.predict(features, type_modifier=baggage.risk_modifier())
            assessment = BaggageAssessment(
                passenger=passenger,
                flight=flight,
                route=route,
                baggage=baggage,
                risk_category=outcome.category,
                risk_score=outcome.probability,
                recommendation=outcome.recommendation,
            )

            self.database.add_record(assessment.as_record())
            self.prediction_value.set(outcome.category)
            self.score_value.set(f"{outcome.probability:.2f}")
            self.recommendation_value.set(outcome.recommendation)
            self.refresh_records()
            messagebox.showinfo("BagSafe AI", "Prediction completed and baggage record saved.")
        except Exception as exc:
            messagebox.showerror("BagSafe AI", str(exc))

    def refresh_records(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.database.fetch_records(self.search_var.get()):
            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row["id"],
                    row["passenger_name"],
                    row["tag_number"],
                    row["flight_number"],
                    f'{row["origin"]}-{row["destination"]}',
                    row["baggage_type"].title(),
                    row["risk_category"],
                    f'{row["risk_score"]:.2f}',
                    row["created_at"],
                ),
            )

    def delete_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("BagSafe AI", "Select a record to delete.")
            return
        for record_id in selected:
            self.database.delete_record(int(record_id))
        self.refresh_records()

    def clear_form(self) -> None:
        defaults = {
            "passenger_name": "",
            "booking_reference": "",
            "tag_number": "",
            "flight_number": "",
            "origin": "",
            "destination": "",
            "layover_minutes": "60",
            "transfer_points": "1",
            "terminal_distance_meters": "850",
            "incoming_delay_minutes": "0",
            "checked_bags": "1",
            "baggage_type": "transfer",
            "priority_status": False,
            "international_transfer": False,
        }
        for key, value in defaults.items():
            self.fields[key].set(value)


def launch_app() -> None:
    app = BagSafeApp()
    app.mainloop()
