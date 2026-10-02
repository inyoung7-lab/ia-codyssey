import json
import unittest
from unittest.mock import patch
from backend.settings import allowed_origins
from backend.firebase import get_firestore_client


class DeploymentTests(unittest.TestCase):
    def test_origins(self):
        with patch.dict("os.environ", {"ALLOWED_ORIGINS":" https://example.test/ ,https://example.test,,"}):
            self.assertEqual(allowed_origins(), ["http://127.0.0.1:5500", "http://localhost:5500", "https://example.test"])
        for value in ["*", "https://example.test/path", "https://user:pass@example.test", "null", "https://example.test:bad"]:
            with patch.dict("os.environ", {"ALLOWED_ORIGINS":value}):
                with self.assertRaises(RuntimeError):
                    allowed_origins()

    def test_firebase_env_and_local_fallback(self):
        for value in [json.dumps({"type":"service_account"}), ""]:
            with patch.dict("os.environ", {"FIREBASE_SERVICE_ACCOUNT_JSON":value, "FIRESTORE_EMULATOR_HOST":""}), patch("backend.firebase.firebase_admin.get_app", side_effect=ValueError), patch("backend.firebase.credentials.Certificate") as certificate, patch("backend.firebase.firebase_admin.initialize_app"), patch("backend.firebase.firestore.client"):
                get_firestore_client()
                argument = certificate.call_args.args[0]
                self.assertEqual(isinstance(argument, dict), bool(value))

    def test_invalid_env_no_fallback_or_leak(self):
        with patch.dict("os.environ", {"FIREBASE_SERVICE_ACCOUNT_JSON":"invalid-sensitive-test", "FIRESTORE_EMULATOR_HOST":""}), patch("backend.firebase.firebase_admin.get_app", side_effect=ValueError), patch("backend.firebase.credentials.Certificate") as certificate:
            with self.assertRaises(RuntimeError) as error:
                get_firestore_client()
            self.assertNotIn("invalid-sensitive-test", str(error.exception))
            certificate.assert_not_called()
