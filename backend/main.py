import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.database.mongo import connect_db, close_db, health_check
from backend.routes import (
    budget_routes, analytics_routes, forecast_routes,
    alert_routes, report_routes, transaction_routes, agent_routes,
    goal_routes, budget_monitor_routes,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Finance Tracker Phase 2...")
    try:
        await connect_db()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.warning("MongoDB not available: %s", e)
        logger.warning("Running without database - some features will be unavailable")
    yield
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title="Personal Finance Tracker Agent - Phase 2",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health():
    db_status = await health_check()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": db_status,
    }


app.include_router(transaction_routes.router)
app.include_router(agent_routes.router)
app.include_router(budget_routes.router)
app.include_router(analytics_routes.router)
app.include_router(forecast_routes.router)
app.include_router(goal_routes.router)
app.include_router(budget_monitor_routes.router)
app.include_router(alert_routes.router)
app.include_router(report_routes.router)


@app.get("/")
async def root():
    return {
        "app": "Personal Finance Tracker Agent - Phase 2",
        "version": "2.0.0",
        "endpoints": [
            "/health",
            "/api/transactions/*",
            "/api/agent/*",
            "/api/budget/*",
            "/api/analytics/*",
            "/api/forecast/*",
            "/api/goals/*",
            "/api/alerts/*",
            "/api/reports/*",
        ],
    }
