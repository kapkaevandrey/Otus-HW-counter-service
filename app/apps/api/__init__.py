import logging

from fastapi import APIRouter

from .middlewares import RequestIdMiddleware
from .ping import router as ping_router
from .v1 import router as v1_router


logger = logging.getLogger(__name__)
main_router = APIRouter()

main_router.include_router(v1_router, prefix="/api")
main_router.include_router(ping_router, include_in_schema=False)


__all__ = ["main_router", "RequestIdMiddleware"]
