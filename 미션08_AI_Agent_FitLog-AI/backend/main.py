from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from google.api_core.exceptions import AlreadyExists
from fastapi.responses import JSONResponse

from backend.schemas.data import WorkoutInput
from backend.routers.data import router as data_router
from backend.routers.conversations import router as conversation_router
from backend.routers.chat import router as chat_router
from backend.services.repository import ServiceError
from backend.settings import allowed_origins

from backend.firebase import get_firestore_client
from backend.workout_analysis import analyze_workouts
from backend.ai_feedback import generate_feedback

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)


app.include_router(data_router)
app.include_router(conversation_router)
app.include_router(chat_router)


@app.exception_handler(ServiceError)
async def handle_service_error(request, error):
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})


@app.post("/workouts", status_code=201)
def create_workout(workout: WorkoutInput):
    record = workout.model_dump()
    try:
        get_firestore_client().collection("workouts").document(workout.date).create(
            record, timeout=30
        )
    except AlreadyExists:
        raise HTTPException(
            status_code=409, detail="해당 날짜의 운동 기록이 이미 존재합니다."
        ) from None
    except Exception:
        raise HTTPException(
            status_code=503, detail="운동 기록을 저장하지 못했습니다."
        ) from None
    return record


@app.get("/")
def root():
    return {"message": "FitLog AI API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


def _read_workouts():
    try:
        collection = get_firestore_client().collection("workouts")
        return [
            document.to_dict()
            for document in collection.order_by("date").stream(timeout=30)
        ]
    except Exception:
        # Never expose raw SDK exceptions or authentication details.
        raise HTTPException(status_code=503, detail="운동 기록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.") from None


@app.get("/workouts")
def get_workouts():
    return _read_workouts()


# Static paths must precede the date parameter route.
@app.get("/workouts/summary")
def get_workouts_summary():
    records = _read_workouts()
    values = [record["value"] for record in records]
    return {
        "total_records": len(records),
        "start_date": records[0]["date"] if records else None,
        "end_date": records[-1]["date"] if records else None,
        "average_value": round(sum(values) / len(values), 2) if values else None,
        "min_value": min(values) if values else None,
        "max_value": max(values) if values else None,
    }


@app.get("/workouts/ai-analysis")
def get_ai_analysis(response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        analysis = analyze_workouts(_read_workouts())
        if not analysis["statistics"]["record_count"]:
            raise HTTPException(status_code=404, detail="분석할 운동 기록이 없습니다.")
        return {**analysis, **generate_feedback(analysis)}
    except ValueError:
        raise HTTPException(status_code=422, detail="운동 기록 형식을 확인해 주세요.") from None


@app.get("/workouts/{date}")
def get_workout(date: str):
    try:
        WorkoutInput.validate_date(date)
    except ValueError:
        raise HTTPException(status_code=422, detail="실제 존재하는 날짜를 YYYY-MM-DD 형식으로 입력해 주세요.") from None
    try:
        document = (
            get_firestore_client()
            .collection("workouts")
            .document(date)
            .get(timeout=30)
        )
    except Exception:
        raise HTTPException(status_code=503, detail="운동 기록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.") from None
    if not document.exists:
        raise HTTPException(status_code=404, detail="해당 날짜의 운동 기록이 없습니다.")
    return document.to_dict()
