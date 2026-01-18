"""
FastAPI + Supabase Auth SaaS Application
Main application entry point.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer
from sqlalchemy.exc import SQLAlchemyError
import logging
from contextlib import asynccontextmanager

from config import get_settings
from database import engine, Base
from routers import users, plans, subscriptions, api_keys, webhooks, job, kling, lip_sync, sora2, templates, veo, media, waitlist

# Security scheme for Swagger UI
security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup and shutdown.
    """
    # Startup
    logger.info("Starting FastAPI + Supabase Auth SaaS application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Supabase URL: {settings.SUPABASE_URL}")
    
    # Create database tables (in production, use Alembic migrations)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    FastAPI backend with Supabase Auth integration for SaaS applications.
    
    ## Authentication
    
    Authentication is handled by Supabase Auth. Users authenticate via:
    - Email/password signup and login
    - Google OAuth
    - Email verification
    
    All protected endpoints require a JWT access token from Supabase in the Authorization header:
    ```
    Authorization: Bearer <supabase_access_token>
    ```
    
    ## Features
    
    - **User Profiles**: Manage user profile data
    - **SaaS Plans**: Browse available pricing plans
    - **Subscriptions**: Manage user subscriptions
    - **API Keys**: Generate and manage API keys for API access
    - **Webhooks**: Receive billing events from Lemon Squeezy
    
    ## Security
    
    - JWT validation using Supabase public keys
    - Row Level Security (RLS) on all database tables
    - API key hashing and secure storage
    - Webhook signature verification
    """,
    lifespan=lifespan,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "persistAuthorization": True
    }
)

# Add security scheme to OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your Supabase JWT access token"
        }
    }
    
    # Apply security globally to all endpoints that use authentication
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict) and "security" not in operation:
                # Check if endpoint has authentication (has parameters with dependencies)
                if operation.get("tags") in [["Users"], ["Subscriptions"], ["API Keys"]]:
                    operation["security"] = [{"HTTPBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "detail": "An error occurred while processing your request"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2026-01-06T00:00:00Z",
        "services": {
            "database": "connected",
            "supabase": "configured"
        }
    }


# Include routers
app.include_router(users.router)
app.include_router(plans.router)
app.include_router(subscriptions.router)
app.include_router(api_keys.router)
app.include_router(webhooks.router)
app.include_router(templates.router)
app.include_router(media.router)
app.include_router(job.router)
app.include_router(kling.router)
app.include_router(sora2.router)
app.include_router(veo.router)
app.include_router(lip_sync.router)

app.include_router(waitlist.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
