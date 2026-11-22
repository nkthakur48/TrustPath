from fastapi import APIRouter

from app.api.routes import analyze, chat, gmail, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(analyze.router, tags=["analyze"])
api_router.include_router(gmail.router, tags=["gmail"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
