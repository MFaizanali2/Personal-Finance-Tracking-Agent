import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from backend.analytics.analyzer import AnalyticsEngine
from backend.analytics.smart_agent import SmartAgent
from backend.alerts.alert_system import AlertSystem
from backend.database.mongo import get_db

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.analyzer = AnalyticsEngine(user_id)
        self.agent = SmartAgent(user_id)
        self.alerts = AlertSystem(user_id)

    async def generate_monthly_report(self, month: Optional[str] = None) -> dict:
        month = month or datetime.utcnow().strftime("%Y-%m")
        logger.info("Generating monthly report for %s", month)

        category_breakdown = await self.analyzer.get_category_breakdown(month)
        budget_vs_actual = await self.analyzer.get_budget_vs_actual(month)
        velocity = await self.analyzer.get_spending_velocity()
        unusual = await self.analyzer.identify_unusual_spending()
        recurring = await self.analyzer.get_recurring_patterns()
        insights_result = await self.agent.generate_insights(30)
        current_alerts = await self.alerts.get_current_alerts()

        db = await get_db()
        cursor = db["transactions"].find({"user_id": self.user_id})
        all_count = await cursor.to_list(length=None)
        total_lifetime = sum(t["amount"] for t in all_count)

        report = {
            "report_type": "monthly",
            "month": month,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_spending": category_breakdown.get("total", 0),
                "transaction_count": len(category_breakdown.get("categories", [])),
                "average_daily": velocity.get("avg_daily", 0),
                "trend": velocity.get("trend", "stable"),
                "lifetime_spending": round(total_lifetime, 2),
            },
            "category_breakdown": category_breakdown,
            "budget_comparison": budget_vs_actual,
            "unusual_spending": unusual,
            "recurring_patterns": recurring,
            "alerts": current_alerts,
            "agent_insights": insights_result,
        }
        return report

    async def generate_custom_report(self, start_date: str, end_date: str) -> dict:
        logger.info("Generating custom report from %s to %s", start_date, end_date)
        db = await get_db()
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        cursor = db["transactions"].find({
            "user_id": self.user_id,
            "date": {"$gte": start, "$lt": end},
        }).sort("date", 1)
        transactions = await cursor.to_list(length=None)

        total = sum(t["amount"] for t in transactions)
        by_category: dict[str, float] = {}
        by_day: dict[str, float] = {}
        for t in transactions:
            cat = t.get("category", "Other")
            by_category[cat] = by_category.get(cat, 0) + t["amount"]
            d = t["date"].strftime("%Y-%m-%d") if hasattr(t["date"], "strftime") else str(t["date"])[:10]
            by_day[d] = by_day.get(d, 0) + t["amount"]

        return {
            "report_type": "custom",
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_spending": round(total, 2),
                "transaction_count": len(transactions),
                "daily_average": round(total / max(len(by_day), 1), 2),
            },
            "category_breakdown": [
                {"category": cat, "amount": round(amt, 2), "percentage": round(amt / total * 100, 1) if total > 0 else 0}
                for cat, amt in sorted(by_category.items(), key=lambda x: -x[1])
            ],
            "daily_spending": [{"date": d, "amount": round(v, 2)} for d, v in sorted(by_day.items())],
        }
