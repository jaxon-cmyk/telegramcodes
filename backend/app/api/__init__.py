from fastapi import APIRouter

from app.api import admin, auth, automation, messages, mt5, telegram

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(telegram.router)
api_router.include_router(messages.router)
api_router.include_router(mt5.router)
api_router.include_router(automation.router)
