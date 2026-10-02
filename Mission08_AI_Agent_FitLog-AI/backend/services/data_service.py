from datetime import date, timedelta

from pydantic import ValidationError

from backend.schemas.data import DataRecord, WorkoutInput, validate_date_id
from backend.services.repository import DateMismatch, InvalidInput, Repository, ServiceError
from backend.workout_analysis import analyze_workouts


class DataService:
    def __init__(self, repository: Repository):
        self.repository = repository

    @staticmethod
    def validate_id(id):
        try:
            return validate_date_id(id)
        except ValueError:
            raise InvalidInput() from None

    def list(self):
        try:
            rows = [DataRecord.model_validate(row).model_dump() for row in self.repository.list()]
            if any(row["id"] != row["date"] for row in rows):
                raise ValueError("Inconsistent document ID")
            return sorted(rows, key=lambda row: row["date"])
        except (ValidationError, ValueError):
            raise ServiceError() from None

    def create(self, body: WorkoutInput):
        row = body.model_dump()
        self.repository.create(body.date, row)
        return {"id": body.date, **row}

    def update(self, id, body: WorkoutInput):
        self.validate_id(id)
        if id != body.date:
            raise DateMismatch()
        row = body.model_dump()
        self.repository.update(id, row)
        return {"id": id, **row}

    def delete(self, id):
        self.validate_id(id)
        self.repository.delete(id)

    def summary(self):
        rows = self.list()
        values = [row["value"] for row in rows]
        active = [value for value in values if value > 0]
        longest = run = 0
        previous_day = None
        for row in rows:
            day = date.fromisoformat(row["date"])
            if row["value"] > 0:
                run = run + 1 if previous_day is not None and (day - previous_day).days == 1 else 1
                longest = max(longest, run)
            else:
                run = 0
            previous_day = day
        trend = {
            "direction": "no_data", "absolute_change": 0, "percent_change": None,
            "recent_total": 0, "previous_total": 0,
            "recent_record_count": 0, "previous_record_count": 0,
            "recent_period": {"start": None, "end": None},
            "previous_period": {"start": None, "end": None},
            "note": "최신 기록일 기준 최근 7일과 직전 7일의 기록된 운동시간 합계 비교. 누락일은 휴식으로 간주하지 않으며 이전 합계가 0이면 변화율은 null입니다.",
        }
        if rows:
            stats = analyze_workouts(rows)["statistics"]
            end = date.fromisoformat(rows[-1]["date"])

            def ago(days):
                return (end - timedelta(days=days)).isoformat() if end.toordinal() > days else None

            trend.update(
                direction={"증가": "increase", "감소": "decrease", "유지": "stable"}[stats["trend"]],
                absolute_change=stats["change_minutes"], percent_change=stats["change_percent"],
                recent_total=stats["recent_7_total_minutes"], previous_total=stats["previous_7_total_minutes"],
                recent_record_count=stats["recent_7_record_count"], previous_record_count=stats["previous_7_record_count"],
                recent_period={"start": ago(6), "end": ago(0)},
                previous_period={"start": ago(13), "end": ago(7)},
            )
        return {
            "period": {"start": rows[0]["date"] if rows else None, "end": rows[-1]["date"] if rows else None},
            "count": len(rows),
            "metrics": {"total": sum(values), "average": round(sum(values) / len(values), 2) if values else None,
                        "max": max(values) if values else None, "min": min(values) if values else None},
            "trend": trend,
            "insights": {
                "workout_days": len(active), "rest_days": len(values) - len(active),
                "workout_day_average": round(sum(active) / len(active), 2) if active else None,
                "longest_workout_streak": longest,
            },
        }
