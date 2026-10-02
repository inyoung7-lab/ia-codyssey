"""One workout per calendar date; minutes are always strict integers."""
from datetime import date as calendar_date
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_date_id(value: str) -> str:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.")
    calendar_date.fromisoformat(value)
    return value


class WorkoutInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: str = Field(strict=True)
    value: int = Field(strict=True, ge=0, le=1440)
    memo: str = Field(strict=True, max_length=500)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        return validate_date_id(value)

    @field_validator("memo", mode="before")
    @classmethod
    def trim_memo(cls, value):
        return value.strip() if isinstance(value, str) else value


class DataRecord(WorkoutInput):
    id: str


class Period(BaseModel):
    start: str | None
    end: str | None


class Metrics(BaseModel):
    total: int
    average: float | None
    max: int | None
    min: int | None


class Trend(BaseModel):
    direction: str
    absolute_change: int
    percent_change: float | None
    recent_total: int
    previous_total: int
    recent_record_count: int
    previous_record_count: int
    recent_period: Period
    previous_period: Period
    note: str


class Insights(BaseModel):
    workout_days: int
    rest_days: int
    workout_day_average: float | None
    longest_workout_streak: int


class DataSummary(BaseModel):
    period: Period
    count: int
    metrics: Metrics
    trend: Trend
    insights: Insights
