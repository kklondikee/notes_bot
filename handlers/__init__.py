from .common import router as common_router
from .notes import router as notes_router
from .tags import router as tags_router
from .search import router as search_router
from .reminders import router as reminders_router
from .media import router as media_router
from .inline import router as inline_router
from .admin import router as admin_router

__all__ = [
    "common_router",
    "notes_router",
    "tags_router",
    "search_router",
    "reminders_router",
    "media_router",
    "inline_router",
    "admin_router"
]