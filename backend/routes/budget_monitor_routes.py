import logging
from fastapi import APIRouter
from backend.analytics.budget_monitor import BudgetMonitorAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/budget-monitor", tags=["Budget Monitor"])


@router.get("/thresholds")
async def budget_thresholds():
    monitor = BudgetMonitorAgent()
    result = await monitor.check_thresholds()
    return {"thresholds": result}


@router.get("/patterns")
async def spending_patterns():
    monitor = BudgetMonitorAgent()
    result = await monitor.analyze_patterns()
    return result


@router.get("/recommendations")
async def recommendations():
    monitor = BudgetMonitorAgent()
    result = await monitor.generate_recommendations()
    return {"recommendations": result}
