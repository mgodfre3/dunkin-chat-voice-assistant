import json
import sqlite3
from pathlib import Path

from crm import CRMRepository

SCHEMA = """
CREATE TABLE customers (
    id TEXT PRIMARY KEY,
    name TEXT,
    rewards_status TEXT,
    loyalty_score INTEGER,
    loyalty_goal INTEGER,
    curbside_preferred INTEGER,
    favorite_items_json TEXT,
    usual_order_json TEXT,
    suggested_sales_json TEXT,
    suggestions_json TEXT,
    last_visit_iso TEXT
);
CREATE TABLE devices (
    mac_address TEXT PRIMARY KEY,
    label TEXT,
    customer_id TEXT
);
"""


def seed_tmp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "crm.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.execute(
            """
            INSERT INTO customers (
                id, name, rewards_status, loyalty_score, loyalty_goal,
                curbside_preferred, favorite_items_json, usual_order_json,
                suggested_sales_json, suggestions_json, last_visit_iso
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "cust-1",
                "Taylor Finch",
                "Gold",
                900,
                1200,
                1,
                json.dumps([{"item": "Iced Latte", "size": "Large", "quantity": 1}]),
                json.dumps([{"item": "Iced Latte", "size": "Large", "quantity": 1}]),
                json.dumps(["Add cold foam"]),
                json.dumps([]),
                "2026-03-09T12:00:00-05:00",
            ),
        )
        conn.execute(
            "INSERT INTO devices (mac_address, label, customer_id) VALUES (?, ?, ?)",
            ("AA:BB:CC:DD:EE:FF", "SUV", "cust-1"),
        )
    return db_path


def test_repo_returns_customer_by_mac(tmp_path):
    db_path = seed_tmp_db(tmp_path)
    repo = CRMRepository(db_path)

    profile = repo.get_customer_by_mac("aa-bb-cc-dd-ee-ff")

    assert profile is not None
    assert profile.name == "Taylor Finch"
    assert profile.bluetooth_devices == ["AA:BB:CC:DD:EE:FF"]
    assert profile.favorite_items[0].item == "Iced Latte"


def test_repo_lists_customers(tmp_path):
    db_path = seed_tmp_db(tmp_path)
    repo = CRMRepository(db_path)

    profiles = repo.list_customers()

    assert len(profiles) == 1
    assert profiles[0].loyalty_score == 900


def test_auto_seeds_from_json(tmp_path):
    db_path = tmp_path / "data" / "crm.db"
    seed_file = tmp_path / "data" / "crm_seed.json"
    seed_file.parent.mkdir(parents=True, exist_ok=True)
    seed_file.write_text(json.dumps({
        "customers": [{
            "id": "cust-auto",
            "name": "Auto Seed",
            "rewards_status": "Silver",
            "loyalty_score": 500,
            "loyalty_goal": 1000,
            "curbside_preferred": False,
            "bluetooth_devices": [{"mac": "11-22-33-44-55-66", "label": "Truck"}],
            "favorite_items": [],
            "usual_order": [],
            "suggested_sales": [],
            "suggestions": [],
            "last_visit_iso": "2026-04-01T10:00:00-05:00",
        }]
    }))

    repo = CRMRepository(db_path, seed_path=seed_file)

    profile = repo.get_customer_by_mac("11:22:33:44:55:66")
    assert profile is not None
    assert profile.name == "Auto Seed"


def test_auto_seed_skipped_when_tables_exist(tmp_path):
    db_path = seed_tmp_db(tmp_path)
    seed_file = tmp_path / "crm_seed.json"
    seed_file.write_text(json.dumps({"customers": []}))

    repo = CRMRepository(db_path, seed_path=seed_file)

    profiles = repo.list_customers()
    assert len(profiles) == 1  # original data preserved, not overwritten
