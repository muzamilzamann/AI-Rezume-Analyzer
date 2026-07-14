"""Aggregated v1 API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import admin, analysis, auth, job_match, resumes

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(resumes.router)
api_router.include_router(analysis.router)
api_router.include_router(job_match.router)
api_router.include_router(admin.router)
