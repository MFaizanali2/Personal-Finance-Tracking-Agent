import logging

from fastapi import APIRouter, Query
from backend.analytics.forecaster import ForecasterAgent
from backend.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/forecast", tags=["Forecast"])


@router.get("/next-month")
async def forecast_next_month(history_months: int = Query(3, ge=1, le=12)):
    cached = CacheManager.get_forecast("default", "next_month", history_months)
    if cached:
        return cached
    forecaster = ForecasterAgent()
    result = await forecaster.forecast_next_month(history_months)
    CacheManager.set_forecast("default", "next_month", result, history_months)
    return result


@router.get("/category/{category}")
async def forecast_by_category(category: str, months: int = Query(3, ge=1, le=12)):
    forecaster = ForecasterAgent()
    result = await forecaster.forecast_by_category(category, months)
    return result


@router.get("/total")
async def predict_total(days: int = Query(30, ge=1, le=365)):
    cached = CacheManager.get_forecast("default", "total", days)
    if cached:
        return cached
    forecaster = ForecasterAgent()
    result = await forecaster.predict_total_spending(days)
    CacheManager.set_forecast("default", "total", result, days)
    return result


@router.get("/trends")
async def spending_trends():
    forecaster = ForecasterAgent()
    result = await forecaster.identify_spending_trends()
    return result


@router.post("/budget-suggestions")
async def budget_suggestions():
    forecaster = ForecasterAgent()
    result = await forecaster.suggest_budget_adjustments()
    return result
