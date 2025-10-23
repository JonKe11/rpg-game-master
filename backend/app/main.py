# backend/app/main.py
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models import Base, engine
from app.api.v1 import api_router

# 🆕 Import WebSocket manager
from app.websocket import manager

settings = get_settings()

# Inicjalizacja bazy
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# 🆕 WebSocket endpoint
@app.websocket("/ws/campaign/{campaign_id}")
async def campaign_websocket(websocket: WebSocket, campaign_id: int):
    """
    WebSocket endpoint for real-time campaign communication
    """
    await manager.connect(websocket, campaign_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Broadcast to all clients in this campaign
            await manager.broadcast(campaign_id, {
                "type": data.get("type", "message"),
                "content": data.get("content"),
                "user_id": data.get("user_id"),
                "character_id": data.get("character_id"),
                "timestamp": data.get("timestamp")
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, campaign_id)
        
        # Notify others that someone left
        await manager.broadcast(campaign_id, {
            "type": "system",
            "content": "A player has disconnected",
            "timestamp": None
        })

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"{settings.app_name} API",
        "version": settings.version,
        "docs": "/docs",
        "modes": ["ai", "multiplayer"]  # 🆕
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}