# backend/app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1 import api_router

# Ten plik agreguje wszystkie endpointy
router = api_router