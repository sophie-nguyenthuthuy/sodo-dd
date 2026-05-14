from fastapi import APIRouter

from app.api.v1 import auth, certificates, due_diligence, webhooks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(certificates.router)
api_router.include_router(due_diligence.router)
api_router.include_router(webhooks.router)
