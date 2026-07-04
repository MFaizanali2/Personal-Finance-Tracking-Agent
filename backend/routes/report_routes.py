import logging
from fastapi import APIRouter, Query
from backend.reports.report_generator import ReportGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/monthly")
async def monthly_report(month: str = None):
    generator = ReportGenerator()
    report = await generator.generate_monthly_report(month)
    return report


@router.get("/custom")
async def custom_report(start_date: str = Query(...), end_date: str = Query(...)):
    generator = ReportGenerator()
    report = await generator.generate_custom_report(start_date, end_date)
    return report


@router.get("/insights")
async def agent_insights(period: int = Query(30, ge=1, le=365)):
    from backend.analytics.smart_agent import SmartAgent
    agent = SmartAgent()
    result = await agent.generate_insights(period)
    return result
