import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from backend.database.mongo import get_db
from backend.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class GoalPlannerAgent:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    async def analyze_all_goals(self) -> dict:
        db = await get_db()
        cursor = db["goals"].find({"user_id": self.user_id, "status": "active"})
        goals = await cursor.to_list(length=None)
        if not goals:
            return {"total_goals": 0, "goals": [], "overall_progress": 0, "insights": []}

        results = []
        total_target = 0
        total_current = 0
        insights = []

        for g in goals:
            target = g["target_amount"]
            current = g.get("current_amount", 0)
            deadline = g["deadline"] if isinstance(g["deadline"], datetime) else datetime.strptime(str(g["deadline"])[:10], "%Y-%m-%d")
            progress = round(min(current / target * 100, 100), 1) if target > 0 else 0
            total_target += target
            total_current += current

            remaining = target - current
            days_left = (deadline - datetime.utcnow()).days
            months_left = max(days_left / 30, 0.5)

            needed_monthly = round(remaining / months_left, 2) if remaining > 0 else 0
            on_track = g.get("monthly_contribution", 0) >= needed_monthly if needed_monthly > 0 else True

            if not on_track:
                insights.append({
                    "goal_id": str(g["_id"]),
                    "name": g["name"],
                    "type": "at_risk",
                    "message": f"Goal '{g['name']}' needs ${needed_monthly:.0f}/month but contributing ${g.get('monthly_contribution', 0):.0f}/month",
                })

            if progress >= 100:
                insights.append({
                    "goal_id": str(g["_id"]),
                    "name": g["name"],
                    "type": "achieved",
                    "message": f"Goal '{g['name']}' achieved! 🎉",
                })
            elif progress >= 75:
                insights.append({
                    "goal_id": str(g["_id"]),
                    "name": g["name"],
                    "type": "nearly_there",
                    "message": f"Goal '{g['name']}' is {progress}% complete - almost there!",
                })

            results.append({
                "goal_id": str(g["_id"]),
                "name": g["name"],
                "target": target,
                "current": current,
                "progress_pct": progress,
                "remaining": round(remaining, 2),
                "deadline": deadline.strftime("%Y-%m-%d"),
                "days_left": max(days_left, 0),
                "needed_monthly": needed_monthly,
                "monthly_contribution": g.get("monthly_contribution", 0),
                "on_track": on_track,
                "status": "completed" if progress >= 100 else "active",
            })

        overall = round(total_current / total_target * 100, 1) if total_target > 0 else 0
        return {
            "total_goals": len(goals),
            "goals": results,
            "overall_progress": overall,
            "total_target": total_target,
            "total_current": total_current,
            "insights": insights,
        }

    async def create_savings_plan(self, goal_id: str) -> dict:
        from bson.objectid import ObjectId
        db = await get_db()
        doc = await db["goals"].find_one({"_id": ObjectId(goal_id), "user_id": self.user_id})
        if not doc:
            return {"error": "Goal not found"}
        target = doc["target_amount"]
        current = doc.get("current_amount", 0)
        remaining = target - current
        deadline = doc["deadline"] if isinstance(doc["deadline"], datetime) else datetime.strptime(str(doc["deadline"])[:10], "%Y-%m-%d")
        days_left = (deadline - datetime.utcnow()).days
        months_left = max(days_left / 30, 0.5)

        per_month = round(remaining / months_left, 2)
        per_week = round(remaining / max(days_left / 7, 1), 2)
        per_day = round(remaining / max(days_left, 1), 2)

        from backend.analytics.analyzer import AnalyticsEngine
        engine = AnalyticsEngine(self.user_id)
        try:
            velocity = await engine.get_spending_velocity()
            daily_avg = velocity.get("avg_daily", 0)
        except Exception:
            daily_avg = 0

        affordable = daily_avg > per_day if daily_avg > 0 else True
        suggestion = "On track" if affordable else "Consider reducing daily spending to meet this goal"

        return {
            "goal_id": goal_id,
            "name": doc["name"],
            "target": target,
            "remaining": remaining,
            "days_left": max(days_left, 0),
            "suggested_monthly": per_month,
            "suggested_weekly": per_week,
            "suggested_daily": per_day,
            "current_daily_spend_avg": daily_avg,
            "affordable": affordable,
            "suggestion": suggestion,
        }
