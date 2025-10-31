# backend/app/core/wiki/__init__.py
"""
Wiki module - FANDOM API integration.

Provides unified interface for accessing wiki data across different universes.
"""

from app.core.wiki.wiki_factory import create_wiki_client, WIKI_CONFIGS, WikiConfig
from app.core.wiki.base_wiki_client import BaseWikiClient

__all__ = [
    'create_wiki_client',
    'BaseWikiClient',
    'WIKI_CONFIGS',
    'WikiConfig'
]