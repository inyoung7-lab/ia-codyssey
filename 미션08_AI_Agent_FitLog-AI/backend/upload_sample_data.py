"""Run from the project root: python -m backend.upload_sample_data."""

import json
from datetime import date, timedelta
from pathlib import Path

from backend.firebase import get_firestore_client

DATA_PATH = Path(__file__).resolve().parent / "data" / "sample_workout_data.json"
COLLECTION = "workouts"


def load_sample_data():
    records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(records, list) or len(records) != 120:
        raise ValueError("Expected 120 records.")
    for index, record in enumerate(records):
        expected_date = (date(2026, 5, 31) + timedelta(days=index)).isoformat()
        if not isinstance(record, dict) or set(record) != {"date", "value", "memo"}:
            raise ValueError("Invalid record fields.")
        if record["date"] != expected_date:
            raise ValueError("Dates must be unique, consecutive and ascending.")
        if type(record["value"]) is not int or record["value"] < 0:
            raise ValueError("Invalid workout duration.")
        if not isinstance(record["memo"], str):
            raise ValueError("Invalid memo.")
    return records


def main():
    stage = "sample validation"
    try:
        records = load_sample_data()
        stage = "client creation"
        client = get_firestore_client()
        print("Firestore connection successful", flush=True)
        collection = client.collection(COLLECTION)
        stage = "upload"
        batch = client.batch()
        for record in records:
            batch.set(collection.document(record["date"]), record)
        print(f"Upload requested: {len(records)}", flush=True)
        batch.commit(timeout=30)
        print("Upload committed: 120", flush=True)
        stage = "readback verification"
        # Read the entire collection, including any unexpected documents.
        documents = list(collection.stream(timeout=30))
        print(f"Firestore document count: {len(documents)}", flush=True)
        expected = {record["date"]: record for record in records}
        actual = {document.id: document.to_dict() for document in documents}
        if len(documents) != 120 or actual != expected:
            raise ValueError("Stored documents do not match the sample exactly.")
        dates = sorted(actual)
        print(f"First date: {dates[0]}")
        print(f"Last date: {dates[-1]}")
        print("Field structure and all 120 records: verified")
    except Exception as error:
        # Print only a stage and exception class, never raw authentication errors.
        print(f"Failed at {stage} ({type(error).__name__}).", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
