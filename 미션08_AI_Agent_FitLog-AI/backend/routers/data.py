from fastapi import APIRouter, Depends, Response

from backend.schemas.data import DataRecord, DataSummary, WorkoutInput
from backend.services.data_service import DataService
from backend.services.repository import FirestoreRepository

router = APIRouter(prefix="/api/data", tags=["data"])


def get_data_service():
    return DataService(FirestoreRepository("data"))


@router.post("", status_code=201, response_model=DataRecord)
def create_data(body: WorkoutInput, service: DataService = Depends(get_data_service)):
    return service.create(body)


@router.get("", response_model=list[DataRecord])
def list_data(service: DataService = Depends(get_data_service)):
    return service.list()


@router.get("/summary", response_model=DataSummary)
def summarize_data(service: DataService = Depends(get_data_service)):
    return service.summary()


@router.put("/{id}", response_model=DataRecord)
def update_data(id: str, body: WorkoutInput, service: DataService = Depends(get_data_service)):
    return service.update(id, body)


@router.delete("/{id}", status_code=204)
def delete_data(id: str, service: DataService = Depends(get_data_service)):
    service.delete(id)
    return Response(status_code=204)
