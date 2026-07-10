from fastapi import APIRouter

from .counters import router as counters_router


router = APIRouter(prefix="/v1")

router.include_router(counters_router)
