from fastapi import APIRouter
from app.api.v1.endpoints import entries, auth, status, doctors, websocket

api_router = APIRouter()
api_router.include_router(entries.router, tags=["entries"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(status.router, tags=["status"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
api_router.include_router(websocket.router, tags=["websocket"])

