"""Pure statistics: no network, credentials, or AI calculations."""

from datetime import date, timedelta


def analyze_workouts(records):
    if not records:
        return {"period": {"start_date": None, "end_date": None}, "statistics": {"record_count": 0}}
    rows = sorted(records, key=lambda row: row["date"])
    dates = [date.fromisoformat(row["date"]) for row in rows]
    if len(set(dates)) != len(dates):
        raise ValueError("Duplicate dates")
    end = dates[-1]
    start = end - timedelta(days=min(29, end.toordinal() - 1))
    selected = [(day, row) for day, row in zip(dates, rows) if start <= day <= end]
    values = [row["value"] for _, row in selected]
    if any(type(value) is not int or not 0 <= value <= 1440 for value in values):
        raise ValueError("Invalid duration")
    active = [value for value in values if value > 0]
    recent = [(day, row) for day, row in selected if (end - day).days <= 6]
    previous = [(day, row) for day, row in selected if 7 <= (end - day).days <= 13]
    recent_total = sum(row["value"] for _, row in recent)
    previous_total = sum(row["value"] for _, row in previous)
    counts = {kind: 0 for kind in ["웨이트", "러닝", "걷기", "복싱", "기타"]}
    longest_active = longest_rest = run_active = run_rest = 0
    previous_day = None
    for day, row in selected:
        if previous_day is not None and day - previous_day != timedelta(days=1):
            run_active = run_rest = 0
        if row["value"] > 0:
            run_active += 1
            run_rest = 0
            # One primary label per active day; first keyword match wins.
            category = next((kind for kind in counts if kind != "기타" and kind in row["memo"]), "기타")
            counts[category] += 1
        else:
            run_rest += 1
            run_active = 0
        longest_active = max(longest_active, run_active)
        longest_rest = max(longest_rest, run_rest)
        previous_day = day
    return {
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "statistics": {
            "record_count": len(values), "missing_days": 30 - len(values),
            "workout_days": len(active), "rest_days": len(values) - len(active),
            "total_minutes": sum(values),
            "average_minutes": round(sum(values) / len(values), 2),
            "active_day_average_minutes": round(sum(active) / len(active), 2) if active else 0,
            "max_minutes": max(values), "min_minutes": min(values),
            "recent_7_total_minutes": recent_total, "previous_7_total_minutes": previous_total,
            "recent_7_record_count": len(recent), "previous_7_record_count": len(previous),
            "change_minutes": recent_total - previous_total,
            "change_percent": round((recent_total - previous_total) / previous_total * 100, 2) if previous_total else None,
            "trend": "증가" if recent_total > previous_total else "감소" if recent_total < previous_total else "유지",
            "longest_workout_streak": longest_active, "longest_rest_streak": longest_rest,
            "current_workout_streak": run_active, "current_rest_streak": run_rest,
            "activity_frequency": counts,
            "classification_note": "운동일 메모의 단순 문자열 분류. 웨이트·러닝·걷기·복싱 순 첫 일치로 하루 한 종류, 나머지는 기타. 정확한 운동 종류를 보장하지 않음.",
            "calculation_note": "단위 분. 평균은 기록된 날 기준(휴식 포함). 누락일은 휴식으로 간주하지 않으며 연속일을 끊음. 연속일은 분석기간 내 한정. 7일 합계는 기록된 날짜만 합산하므로 누락 시 비교에 주의. 이전 합계 0이면 변화율은 null.",
        },
    }
