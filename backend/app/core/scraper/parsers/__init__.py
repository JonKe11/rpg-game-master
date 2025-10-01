# backend/app/core/scraper/parsers/__init__.py
from .base_parser import BaseParser
from .wookieepedia_parser import WookieepediaParser

__all__ = ['BaseParser', 'WookieepediaParser']