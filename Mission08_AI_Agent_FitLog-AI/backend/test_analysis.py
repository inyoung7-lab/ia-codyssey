import unittest
from datetime import date, timedelta

from backend.workout_analysis import analyze_workouts


class StatisticsTests(unittest.TestCase):
    def test_calendar_totals_and_sorting(self):
        rows = [{"date": (date(2026, 8, 29) + timedelta(days=i)).isoformat(), "value": 10 if i % 2 else 0, "memo": "러닝"} for i in range(31)]
        result = analyze_workouts(list(reversed(rows)))
        self.assertEqual(result['period'], {'start_date': '2026-08-30', 'end_date': '2026-09-28'})
        s = result['statistics']
        for key, expected in {'record_count':30, 'workout_days':15, 'rest_days':15, 'total_minutes':150, 'average_minutes':5, 'active_day_average_minutes':10, 'recent_7_total_minutes':30, 'previous_7_total_minutes':40, 'change_minutes':-10, 'change_percent':-25, 'longest_workout_streak':1, 'longest_rest_streak':1, 'current_rest_streak':1}.items():
            self.assertEqual(s[key], expected, key)
        self.assertEqual(s['activity_frequency']['러닝'],15)

    def test_gaps_classification_and_zero_baseline(self):
        rows = [{'date':'2026-09-25','value':20,'memo':'웨이트-가슴 러닝'}, {'date':'2026-09-27','value':10,'memo':'스트레칭'}, {'date':'2026-09-28','value':0,'memo':'휴식'}]
        s = analyze_workouts(rows)['statistics']
        self.assertEqual(s['missing_days'],27)
        self.assertEqual(s['longest_workout_streak'],1)
        self.assertEqual(s['activity_frequency']['웨이트'],1)
        self.assertEqual(s['activity_frequency']['기타'],1)
        self.assertIsNone(s['change_percent'])
        self.assertEqual(s['average_minutes'],10)
        self.assertEqual(s['active_day_average_minutes'],15)

    def test_empty_and_rest_only(self):
        self.assertEqual(analyze_workouts([])['statistics']['record_count'],0)
        s=analyze_workouts([{'date':'2026-09-28','value':0,'memo':'휴식'}])['statistics']
        self.assertEqual(s['active_day_average_minutes'],0)
        self.assertEqual(s['rest_days'],1)
        self.assertEqual(sum(s['activity_frequency'].values()),0)


if __name__ == "__main__":
    unittest.main()
