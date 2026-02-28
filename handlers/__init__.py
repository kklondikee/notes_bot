from .common import router as common_router
from .notes import router as notes_router
from .media import router as media_router
from .weather import router as weather_router
from .admin import router as admin_router   # добавить

__all__ = [
    "common_router",
    "notes_router",
    "media_router",
    "weather_router",
    "admin_router",   # добавить
]