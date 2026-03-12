"""Data models for the drive-thru lane simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

__all__ = [
    "DriveThruStatus",
    "DriveThruCar",
    "DriveThruEvent",
    "DriveThruMetrics",
]


class DriveThruStatus(str, Enum):
    ARRIVED = "arrived"
    ORDERING = "ordering"
    PAYING = "paying"
    PICKUP = "pickup"
    COMPLETE = "complete"


@dataclass
class DriveThruCar:
    car_id: str
    status: DriveThruStatus = DriveThruStatus.ARRIVED
    mac_address: Optional[str] = None
    session_id: Optional[str] = None
    crm_customer_id: Optional[str] = None
    crm_summary: Optional[Dict[str, Any]] = None
    order_total: Optional[float] = None
    wait_target_seconds: int = 600
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> Dict[str, Any]:
        payload = {
            "carId": self.car_id,
            "status": self.status.value,
            "macAddress": self.mac_address,
            "sessionId": self.session_id,
            "crmCustomerId": self.crm_customer_id,
            "waitSeconds": self.wait_seconds,
            "waitColor": self.wait_color,
            "orderTotal": self.order_total,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "crmSummary": self.crm_summary or {},
        }
        return payload

    @property
    def wait_seconds(self) -> int:
        return max(0, int((datetime.now(timezone.utc) - self.created_at).total_seconds()))

    @property
    def wait_color(self) -> str:
        if self.wait_seconds < 120:
            return "green"
        if self.wait_seconds < 300:
            return "yellow"
        return "red"


@dataclass
class DriveThruMetrics:
    cars_in_queue: int
    avg_wait_seconds: float
    orders_per_hour: float
    recognized_percent: float
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "carsInQueue": self.cars_in_queue,
            "avgWaitSeconds": self.avg_wait_seconds,
            "ordersPerHour": self.orders_per_hour,
            "recognizedPercent": self.recognized_percent,
            "timestamp": self.last_updated.isoformat(),
        }


@dataclass
class DriveThruEvent:
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> Dict[str, Any]:
        data = {"type": self.event_type, **self.payload}
        data["timestamp"] = self.timestamp.isoformat()
        return data
