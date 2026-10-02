import unittest
from backend.services.data_service import DataService
from backend.schemas.data import DataSummary
from backend.test_mission_api import MemoryRepository


class InsightTests(unittest.TestCase):
    def summary(self, rows):
        repo = MemoryRepository()
        for day, value in rows:
            repo.create(day, {"date": day, "value": value, "memo": "test"})
        return DataSummary.model_validate(DataService(repo).summary()).model_dump()

    def test_normal_all_period_not_last_thirty_days(self):
        s = self.summary([("2026-01-01", 20), ("2026-01-02", 40), ("2026-09-28", 60)])
        self.assertEqual(s["insights"], {"workout_days": 3, "rest_days": 0, "workout_day_average": 40, "longest_workout_streak": 2})
        self.assertEqual(s["count"], 3)

    def test_rest_and_gap_break_streak(self):
        s = self.summary([("2026-01-01", 10), ("2026-01-02", 10), ("2026-01-03", 0), ("2026-01-04", 10), ("2026-01-06", 10), ("2026-01-07", 10), ("2026-01-08", 10)])
        self.assertEqual(s["insights"]["longest_workout_streak"], 3)
        self.assertEqual(s["insights"]["rest_days"], 1)
        self.assertEqual(s["insights"]["workout_days"], 6)

    def test_empty(self):
        self.assertEqual(self.summary([])["insights"], {"workout_days": 0, "rest_days": 0, "workout_day_average": None, "longest_workout_streak": 0})

    def test_rest_only(self):
        self.assertEqual(self.summary([("2026-01-01", 0)])["insights"], {"workout_days": 0, "rest_days": 1, "workout_day_average": None, "longest_workout_streak": 0})

    def test_rounding_and_calendar_boundary(self):
        s = self.summary([("2025-12-31", 10), ("2026-01-01", 10), ("2026-01-02", 11)])
        self.assertEqual(s["insights"]["workout_day_average"], 10.33)
        self.assertEqual(s["insights"]["longest_workout_streak"], 3)
