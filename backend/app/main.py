# backend/app/main.py
"""
Application entry point.

This module sets up the FastAPI application, includes all routers,
configures middleware, and defines startup/shutdown events.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ORIGINS, APP_NAME, APP_VERSION
from app.database.database import init_db_pool, close_db_pool
from app.api.endpoints import clients, providers, payments, documents

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

def create_app():
    """
    Create and configure the FastAPI application.
    
    Returns: Configured FastAPI application instance
    """
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description="API for 401k Payment Management System",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(clients.router)
    app.include_router(providers.router)
    app.include_router(payments.router)
    app.include_router(documents.router)
    
    # Register event handlers
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)
    
    return app

async def startup_event():
    """Initialize application resources on startup."""
    logger.info("Starting up application...")
    
    # Initialize database connection pool
    await init_db_pool()
    
    logger.info("Application startup complete")

async def shutdown_event():
    """Clean up resources on application shutdown."""
    logger.info("Shutting down application...")
    
    # Close database connections
    await close_db_pool()
    
    logger.info("Application shutdown complete")

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)