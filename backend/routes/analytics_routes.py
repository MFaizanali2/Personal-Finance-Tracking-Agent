import logging

from fastapi import APIRouter, Query
from backend.analytics.analyzer import AnalyticsEngine
from backend.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/spending-trend")
async def spending_trend(days: int = Query(30, ge=1, le=365)):
    cached = CacheManager.get_analytics("default", "spending_trend", days)
    if cached:
        return cached
    analyzer = AnalyticsEngine()
    result = await analyzer.get_spending_trend(days)
    CacheManager.set_analytics("default", "spending_trend", result, days)
    return {"trend": result}


@router.get("/category-breakdown")
async def category_breakdown(month: str = None):
    cached = CacheManager.get_analytics("default", "category_breakdown", month or "current")
    if cached:
        return cached
    analyzer = AnalyticsEngine()
    result = await analyzer.get_category_breakdown(month)
    CacheManager.set_analytics("default", "category_breakdown", result, month or "current")
    return result


@router.get("/spending-velocity")
async def spending_velocity():
    cached = CacheManager.get_analytics("default", "spending_velocity")
    if cached:
        return cached
    analyzer = AnalyticsEngine()
    result = await analyzer.get_spending_velocity()
    CacheManager.set_analytics("default", "spending_velocity", result)
    return result


@router.get("/unusual-spending")
async def unusual_spending():
    analyzer = AnalyticsEngine()
    result = await analyzer.identify_unusual_spending()
    return {"unusual_transactions": result}


@router.get("/monthly-comparison")
async def monthly_comparison(months: int = Query(3, ge=2, le=12)):
    cached = CacheManager.get_analytics("default", "monthly_comparison", months)
    if cached:
        return cached
    analyzer = AnalyticsEngine()
    result = await analyzer.get_monthly_comparison(months)
    CacheManager.set_analytics("default", "monthly_comparison", result, months)
    return {"comparisons": result}


@router.get("/top-days")
async def top_spending_days(days: int = Query(90, ge=7, le=365)):
    analyzer = AnalyticsEngine()
    result = await analyzer.get_top_spending_days(days)
    return {"top_days": result}


@router.get("/recurring")
async def recurring_patterns():
    analyzer = AnalyticsEngine()
    result = await analyzer.get_recurring_patterns()
    return {"recurring": result}


@router.get("/savings-rate")
async def savings_rate(month: str = None, income: float = Query(0, ge=0)):
    analyzer = AnalyticsEngine()
    result = await analyzer.get_savings_rate(month, income)
    return result


@router.get("/budget-vs-actual")
async def budget_vs_actual(month: str = None):
    if not month:
        from datetime import datetime
        month = datetime.utcnow().strftime("%Y-%m")
    analyzer = AnalyticsEngine()
    result = await analyzer.get_budget_vs_actual(month)
    return result
