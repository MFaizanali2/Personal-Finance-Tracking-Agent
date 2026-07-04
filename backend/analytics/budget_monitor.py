import logging
from datetime import datetime, timedelta
from statistics import mean

from backend.database.mongo import get_db

logger = logging.getLogger(__name__)


class BudgetMonitorAgent:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    async def _get_transactions(self, days: int = 30) -> list[dict]:
        db = await get_db()
        since = datetime.utcnow() - timedelta(days=days)
        cursor = db["transactions"].find({"user_id": self.user_id, "date": {"$gte": since}})
        return await cursor.to_list(length=None)

    async def check_thresholds(self) -> list[dict]:
        db = await get_db()
        month = datetime.utcnow().strftime("%Y-%m")
        budget_doc = await db["budgets"].find_one({"user_id": self.user_id, "month": month})
        if not budget_doc:
            return []
        budgets = budget_doc["budgets"]
        transactions = await self._get_transactions(30)
        actuals: dict[str, float] = {}
        for t in transactions:
            cat = t.get("category", "Other")
            actuals[cat] = actuals.get(cat, 0) + t["amount"]
        results = []
        for cat, budget_amt in budgets.items():
            if budget_amt <= 0:
                continue
            actual = actuals.get(cat, 0)
            pct = round(actual / budget_amt * 100, 1)
            results.append({
                "category": cat,
                "budget": budget_amt,
                "actual": round(actual, 2),
                "percentage": pct,
                "status": "over" if pct > 100 else "warning" if pct > 80 else "warning" if pct > 60 else "ok",
            })
        return sorted(results, key=lambda r: -r["percentage"])

    async def analyze_patterns(self) -> dict:
        transactions = await self._get_transactions(60)
        if not transactions:
            return {"patterns": [], "insights": []}
        weekly: dict[str, float] = {}
        for t in transactions:
            d = t["date"]
            week = d.strftime("%Y-W%W") if hasattr(d, "strftime") else ""
            weekly[week] = weekly.get(week, 0) + t["amount"]
        weeks = sorted(weekly.keys())
        patterns = []
        if len(weeks) >= 2:
            first_half = sum(weekly[w] for w in weeks[:len(weeks)//2]) / max(len(weeks)//2, 1)
            second_half = sum(weekly[w] for w in weeks[len(weeks)//2:]) / max(len(weeks) - len(weeks)//2, 1)
            if second_half > first_half * 1.2:
                patterns.append({"type": "increasing", "message": "Weekly spending is trending upward", "change_pct": round((second_half/first_half - 1) * 100, 1)})
            elif first_half > second_half * 1.2:
                patterns.append({"type": "decreasing", "message": "Weekly spending is trending downward", "change_pct": round((first_half/second_half - 1) * 100, 1)})
            else:
                patterns.append({"type": "stable", "message": "Weekly spending is stable"})
        return {"patterns": patterns, "weekly_totals": {w: round(v, 2) for w, v in weekly.items()}}

    async def generate_recommendations(self) -> list[dict]:
        recs = []
        thresholds = await self.check_thresholds()
        for t in thresholds:
            if t["status"] == "over":
                recs.append({
                    "type": "over_budget",
                    "category": t["category"],
                    "severity": "critical",
                    "message": f"Over budget in '{t['category']}' by ${t['actual'] - t['budget']:.2f} ({t['percentage']}%)",
                    "suggestion": f"Reduce '{t['category']}' spending or reallocate budget",
                })
            elif t["percentage"] > 80:
                recs.append({
                    "type": "near_limit",
                    "category": t["category"],
                    "severity": "warning",
                    "message": f"'{t['category']}' at {t['percentage']}% of budget",
                    "suggestion": f"Watch '{t['category']}' - only ${t['budget'] - t['actual']:.2f} remaining",
                })
        transactions = await self._get_transactions(30)
        if transactions:
            amts = [t["amount"] for t in transactions]
            avg_amt = mean(amts)
            high_count = sum(1 for a in amts if a > avg_amt * 2)
            if high_count > 2:
                recs.append({
                    "type": "frequent_large",
                    "severity": "info",
                    "message": f"{high_count} transactions exceed 2x your average",
                    "suggestion": "Review large transactions for potential savings",
                })
        return recs
