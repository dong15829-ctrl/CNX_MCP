from __future__ import annotations

from fastapi import APIRouter

from di_es_dashboard_api.routes.admin import router as admin_router
from di_es_dashboard_api.routes.public import router as public_router


router = APIRouter()
router.include_router(public_router, tags=["public"])
router.include_router(admin_router, tags=["admin"])

