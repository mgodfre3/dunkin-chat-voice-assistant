"""Lightweight SQLite repository for CRM sample data."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from .models import CustomerFavoriteItem, CustomerProfile, CustomerSuggestion

logger = logging.getLogger(__name__)


class CRMRepository:
    """Provides read-only access to CRM customer profiles."""

    def __init__(self, db_path: Path | str):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls, db_path: str | None) -> "CRMRepository":
        if db_path is None:
            db_path = Path(__file__).resolve().parent / ".." / "data" / "crm.db"
        return cls(Path(db_path).resolve())

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def list_customers(self) -> list[CustomerProfile]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT c.*, COALESCE(d.devices, '[]') AS devices
                FROM customers c
                LEFT JOIN (
                    SELECT customer_id, json_group_array(mac_address) AS devices
                    FROM devices
                    GROUP BY customer_id
                ) d ON c.id = d.customer_id
                ORDER BY c.name
                """
            ).fetchall()
        return [self._row_to_profile(row) for row in rows]

    def get_customer(self, customer_id: str) -> Optional[CustomerProfile]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT c.*, COALESCE(d.devices, '[]') AS devices
                FROM customers c
                LEFT JOIN (
                    SELECT customer_id, json_group_array(mac_address) AS devices
                    FROM devices
                    GROUP BY customer_id
                ) d ON c.id = d.customer_id
                WHERE c.id = ?
                """,
                (customer_id,),
            ).fetchone()
        return self._row_to_profile(row) if row else None

    def get_customer_by_mac(self, mac_address: str) -> Optional[CustomerProfile]:
        normalized = mac_address.replace("-", ":").upper()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT c.*, COALESCE(d.devices, '[]') AS devices
                FROM customers c
                INNER JOIN devices dv ON dv.customer_id = c.id
                LEFT JOIN (
                    SELECT customer_id, json_group_array(mac_address) AS devices
                    FROM devices
                    GROUP BY customer_id
                ) d ON c.id = d.customer_id
                WHERE dv.mac_address = ?
                """,
                (normalized,),
            ).fetchone()
        return self._row_to_profile(row) if row else None

    def _row_to_profile(self, row: sqlite3.Row) -> CustomerProfile:
        favorite_items = self._safe_load_list(row["favorite_items_json"])
        usual_order = self._safe_load_list(row["usual_order_json"])
        suggestions = self._safe_load_list(row["suggestions_json"], default=[])
        suggestion_models = [CustomerSuggestion(**payload) for payload in suggestions]
        return CustomerProfile(
            id=row["id"],
            name=row["name"],
            rewards_status=row["rewards_status"],
            loyalty_score=row["loyalty_score"],
            loyalty_goal=row["loyalty_goal"],
            curbside_preferred=bool(row["curbside_preferred"]),
            bluetooth_devices=self._safe_load_list(row["devices"], default=[]),
            favorite_items=[CustomerFavoriteItem(**payload) for payload in favorite_items],
            usual_order=[CustomerFavoriteItem(**payload) for payload in usual_order],
            suggested_sales=self._safe_load_list(row["suggested_sales_json"], default=[]),
            suggestions=suggestion_models,
            last_visit_iso=row["last_visit_iso"],
        )

    @staticmethod
    def _safe_load_list(raw: Optional[str], default: Iterable | None = None) -> list:
        if raw in (None, ""):
            return list(default or [])
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else list(default or [])
        except json.JSONDecodeError:
            logger.warning("Failed to parse CRM JSON payload: %s", raw)
            return list(default or [])
