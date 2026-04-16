from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Passenger:
    full_name: str
    booking_reference: str


@dataclass(slots=True)
class FlightSegment:
    flight_number: str
    origin: str
    destination: str


@dataclass(slots=True)
class TransferRoute:
    layover_minutes: int
    transfer_points: int
    terminal_distance_meters: int
    incoming_delay_minutes: int
    international_transfer: bool

    def as_features(self) -> dict[str, int]:
        return {
            "layover_minutes": self.layover_minutes,
            "transfer_points": self.transfer_points,
            "terminal_distance_meters": self.terminal_distance_meters,
            "incoming_delay_minutes": self.incoming_delay_minutes,
            "international_transfer": int(self.international_transfer),
        }


class Baggage(ABC):
    def __init__(
        self,
        tag_number: str,
        checked_bags: int,
        priority_status: bool = False,
    ) -> None:
        self._tag_number = tag_number.strip().upper()
        self._checked_bags = checked_bags
        self._priority_status = priority_status

    @property
    def tag_number(self) -> str:
        return self._tag_number

    @property
    def checked_bags(self) -> int:
        return self._checked_bags

    @property
    def priority_status(self) -> bool:
        return self._priority_status

    @property
    @abstractmethod
    def baggage_type(self) -> str:
        """Concrete baggage type label."""

    @abstractmethod
    def risk_modifier(self) -> float:
        """Type-specific modifier used by the prediction workflow."""

    def as_features(self) -> dict[str, object]:
        return {
            "checked_bags": self.checked_bags,
            "priority_status": int(self.priority_status),
            "baggage_type": self.baggage_type,
        }


class TransferBag(Baggage):
    @property
    def baggage_type(self) -> str:
        return "transfer"

    def risk_modifier(self) -> float:
        return 0.12


class PriorityBag(Baggage):
    @property
    def baggage_type(self) -> str:
        return "priority"

    def risk_modifier(self) -> float:
        return -0.1


class FragileBag(Baggage):
    @property
    def baggage_type(self) -> str:
        return "fragile"

    def risk_modifier(self) -> float:
        return 0.06


def build_baggage(
    tag_number: str,
    baggage_type: str,
    checked_bags: int,
    priority_status: bool,
) -> Baggage:
    kind = baggage_type.lower().strip()
    if kind == "priority":
        return PriorityBag(tag_number=tag_number, checked_bags=checked_bags, priority_status=True)
    if kind == "fragile":
        return FragileBag(tag_number=tag_number, checked_bags=checked_bags, priority_status=priority_status)
    return TransferBag(tag_number=tag_number, checked_bags=checked_bags, priority_status=priority_status)


@dataclass(slots=True)
class BaggageAssessment:
    passenger: Passenger
    flight: FlightSegment
    route: TransferRoute
    baggage: Baggage
    risk_category: str
    risk_score: float
    recommendation: str
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def as_record(self) -> dict[str, object]:
        payload = {
            "passenger_name": self.passenger.full_name,
            "booking_reference": self.passenger.booking_reference,
            "tag_number": self.baggage.tag_number,
            "flight_number": self.flight.flight_number,
            "origin": self.flight.origin,
            "destination": self.flight.destination,
            "risk_category": self.risk_category,
            "risk_score": round(self.risk_score, 3),
            "recommendation": self.recommendation,
            "created_at": self.created_at,
        }
        payload.update(self.route.as_features())
        payload.update(self.baggage.as_features())
        return payload

