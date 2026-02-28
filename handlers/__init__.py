from .common import router as common_router
from .notes import router as notes_router
from .media import router as media_router

__all__ = [
    "common_router",
    "notes_router",
    "media_router",
]