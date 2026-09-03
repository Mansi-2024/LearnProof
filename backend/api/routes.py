"""Root API router — mounts all sub-routers under /api."""

from fastapi import APIRouter

from api.auth import router as auth_router
from api.artifacts import router as artifacts_router
from api.attempts import router as attempts_router
from api.mastery import router as mastery_router
from api.verification import router as verification_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(artifacts_router)
api_router.include_router(attempts_router)
api_router.include_router(mastery_router)
api_router.include_router(verification_router)

