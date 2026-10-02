"""Firebase authentication and a reusable Firestore client."""

import os
import json
from pathlib import Path
from threading import Lock

import firebase_admin
from firebase_admin import credentials, firestore

_INITIALIZATION_LOCK = Lock()
_KEY_PATH = Path(__file__).resolve().parent / "firebase-service-account.json"


def get_firestore_client():
    """Use the local service account without logging credential contents."""
    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        raise RuntimeError("Cloud Firestore is required; emulator is configured.")
    with _INITIALIZATION_LOCK:
        try:
            app = firebase_admin.get_app()
        except ValueError:
            try:
                raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
                account = json.loads(raw) if raw else str(_KEY_PATH)
                if raw and not isinstance(account, dict):
                    raise ValueError("Invalid credential format")
                app = firebase_admin.initialize_app(credentials.Certificate(account))
            except Exception:
                raise RuntimeError("Firebase credential configuration is invalid.") from None
    return firestore.client(app=app)


if __name__ == "__main__":
    try:
        get_firestore_client()
    except Exception as error:
        # Raw SDK exceptions may contain credential details; never print them.
        print(f"Firestore client creation failed ({type(error).__name__}).")
        raise SystemExit(1) from None
    print("Firestore connection successful")
