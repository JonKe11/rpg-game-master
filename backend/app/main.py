
"""
FastAPI Main Application with Startup Prefetch.

Features:
- Lifespan management (startup/shutdown hooks)
- Background prefetch task (non-blocking)
- WebSocket support for multiplayer
- Exception handling
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.endpoints import friends
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models import Base, engine
from app.api.v1 import api_router


from app.services.startup_prefetch_service import startup_prefetch_all


from app.websocket import manager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


Base.metadata.create_all(bind=engine)






@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles:
    - Startup: Background prefetch, initialization
    - Shutdown: Cleanup, graceful shutdown
    """
    
    logger.info("="*60)
    logger.info("🚀 Starting RPG Game Master Backend")
    logger.info("="*60)
    logger.info(f"App: {settings.app_name} v{settings.version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    logger.info("="*60)
    
    
    logger.info("\n🎯 Initiating background prefetch...")
    logger.info("   (API will be available immediately!)\n")
    
    
    prefetch_task = asyncio.ensure_future(
        startup_prefetch_all(
            universe='star_wars',
            force_refresh=False,  
            prefetch_images=True,
            image_workers=20  
        )
    )
    
    logger.info("✅ API is now READY!")
    logger.info("   Docs: http://localhost:8000/docs")
    logger.info("   Prefetch running in background...\n")
    
    yield  
    
    
    logger.info("\n" + "="*60)
    logger.info("👋 Shutting down RPG Game Master Backend")
    logger.info("="*60)
    
    
    if not prefetch_task.done():
        logger.info("⏸️  Cancelling background prefetch...")
        prefetch_task.cancel()
        try:
            await prefetch_task
        except asyncio.CancelledError:
            logger.info("✅ Prefetch cancelled")
    
    logger.info("✅ Shutdown complete\n")






app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  
)






app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )






app.include_router(api_router, prefix="/api/v1")
app.include_router(friends.router, prefix="/api/v1/friends", tags=["friends"])




@app.websocket("/ws/campaign/{campaign_id}")
async def campaign_websocket(websocket: WebSocket, campaign_id: int):
    """
    WebSocket endpoint for real-time campaign communication.
    
    Args:
        websocket: WebSocket connection
        campaign_id: Campaign ID to join
    """
    await manager.connect(websocket, campaign_id)
    
    try:
        while True:
            
            data = await websocket.receive_json()
            
            
            await manager.broadcast(campaign_id, {
                "type": data.get("type", "message"),
                "content": data.get("content"),
                "user_id": data.get("user_id"),
                "character_id": data.get("character_id"),
                "timestamp": data.get("timestamp")
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, campaign_id)
        
        
        await manager.broadcast(campaign_id, {
            "type": "system",
            "content": "A player has disconnected",
            "timestamp": None
        })





@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"{settings.app_name} API",
        "version": settings.version,
        "docs": "/docs",
        "modes": ["ai", "multiplayer"],
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/prefetch/status")
async def prefetch_status():
    """
    Get prefetch status.
    
    Returns progress of background prefetch task.
    """
    from app.services.startup_prefetch_service import get_prefetch_service
    
    service = get_prefetch_service()
    progress = service.get_progress()
    
    return {
        "is_complete": service.is_prefetch_complete(),
        "progress": progress
    }