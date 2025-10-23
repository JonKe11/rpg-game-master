# backend/app/websocket/__init__.py
from .campaign_ws import manager, ConnectionManager

__all__ = ["manager", "ConnectionManager"]