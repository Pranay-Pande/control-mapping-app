"""
Main API router that aggregates all endpoint routers.
"""
from fastapi import APIRouter

from app.api.endpoints import upload, configure, mapping, download, providers, debug

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(upload.router, tags=["Upload"])
api_router.include_router(configure.router, tags=["Configure"])
api_router.include_router(mapping.router, tags=["Mapping"])
api_router.include_router(download.router, tags=["Download"])
api_router.include_router(providers.router, tags=["Providers"])
api_router.include_router(debug.router, tags=["Debug"])
