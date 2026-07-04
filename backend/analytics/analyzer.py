import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

from backend.database.mongo import get_db

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    async def _get_transactions(self, days: Optional[int] = None) -> list[dict]:
        db = await get_db()
        query: dict[str, Any] = {"user_id": self.user_id}
        if days is not None:
            since = datetime.utcnow() - timedelta(days=days)
            query["date"] = {"$gte": since}
        cursor = db["transactions"].find(query).sort("date", -1)
        return await cursor.to_list(length=None)

    async def _get_month_transactions(self, month: str) -> list[dict]:
        db = await get_db()
        start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
        if month[5:] == "12":
            end = datetime.strptime(f"{int(month[:4]) + 1}-01-01", "%Y-%m-%d")
        else:
            end = datetime.strptime(f"{month[:4]}-{int(month[5:]) + 1:02d}-01", "%Y-%m-%d")
        cursor = db["transactions"].find({
            "user_id": self.user_id,
            "date": {"$gte": start, "$lt": end},
        }).sort("date", -1)
        return await cursor.to_list(length=None)

    async def get_spending_trend(self, days: int = 30) -> list[dict]:
        transactions = await self._get_transactions(days)
        daily: dict[str, float] = {}
        for t in transactions:
            d = t["date"].strftime("%Y-%m-%d") if hasattr(t["date"], "strftime") else str(t["date"])[:10]
            daily[d] = daily.get(d, 0) + t["amount"]
        result = [{"date": d, "amount": round(v, 2)} for d, v in sorted(daily.items())]
        return result

    async def get_category_breakdown(self, month: Optional[str] = None) -> dict:
        if month:
            transactions = await self._get_month_transactions(month)
        else:
            transactions = await self._get_transactions(30)
        by_category: dict[str, float] = {}
        for t in transactions:
            cat = t.get("category", "Other")
            by_category[cat] = by_category.get(cat, 0) + t["amount"]
        total = sum(by_category.values()) or 1
        breakdown = [
            {"category": cat, "amount": round(amt, 2), "percentage": round(amt / total * 100, 1)}
            for cat, amt in sorted(by_category.items(), key=lambda x: -x[1])
        ]
        return {"total": round(total, 2), "categories": breakdown}

    async def get_spending_velocity(self) -> dict:
        transactions = await self._get_transactions(30)
        if not transactions:
            return {"avg_daily": 0, "trend": "stable", "total": 0}
        total = sum(t["amount"] for t in transactions)
        avg_daily = round(total / 30, 2)
        first_half = sum(t["amount"] for t in transactions if t["date"] < datetime.utcnow() - timedelta(days=15))
        second_half = sum(t["amount"] for t in transactions if t["date"] >= datetime.utcnow() - timedelta(days=15))
        trend = "increasing" if second_half > first_half else "decreasing" if first_half > second_half else "stable"
        return {"avg_daily": avg_daily, "trend": trend, "total": round(total, 2)}

    async def get_savings_rate(self, month: Optional[str] = None, income: float = 0) -> dict:
        transactions = await self._get_month_transactions(month or datetime.utcnow().strftime("%Y-%m"))
        total_spent = sum(t["amount"] for t in transactions)
        if income <= 0:
            return {"savings_rate": None, "total_spent": round(total_spent, 2), "message": "Income data required"}
        rate = round((income - total_spent) / income * 100, 1)
        return {"savings_rate": rate, "total_spent": round(total_spent, 2), "income": income}

    async def get_budget_vs_actual(self, month: Optional[str] = None) -> dict:
        from backend.database.mongo import get_db
        db = await get_db()
        month = month or datetime.utcnow().strftime("%Y-%m")
        budget_doc = await db["budgets"].find_one({"user_id": self.user_id, "month": month})
        budget = budget_doc["budgets"] if budget_doc else {}
        transactions = await self._get_month_transactions(month)
        actuals: dict[str, float] = {}
        for t in transactions:
            cat = t.get("category", "Other")
            actuals[cat] = actuals.get(cat, 0) + t["amount"]
        all_cats = set(list(budget.keys()) + list(actuals.keys()))
        comparisons = []
        total_budget = 0
        total_actual = 0
        for cat in sorted(all_cats):
            b = budget.get(cat, 0)
            a = round(actuals.get(cat, 0), 2)
            total_budget += b
            total_actual += a
            pct = round(a / b * 100, 1) if b > 0 else 0
            comparisons.append({"category": cat, "budget": b, "actual": a, "percentage_used": pct, "remaining": round(b - a, 2)})
        return {
            "month": month,
            "total_budget": total_budget,
            "total_actual": round(total_actual, 2),
            "categories": comparisons,
        }

    async def identify_unusual_spending(self) -> list[dict]:
        transactions = await self._get_transactions(30)
        if not transactions:
            return []
        amounts = [t["amount"] for t in transactions]
        avg = sum(amounts) / len(amounts)
        threshold = avg * 2
        unusual = []
        for t in transactions:
            if t["amount"] > threshold:
                unusual.append({
                    "_id": str(t["_id"]),
                    "amount": t["amount"],
                    "category": t.get("category", ""),
                    "description": t.get("description", ""),
                    "date": t["date"].strftime("%Y-%m-%d") if hasattr(t["date"], "strftime") else str(t["date"])[:10],
                    "reason": f"Amount ${t['amount']:.2f} exceeds 2x average (${avg:.2f})",
                })
        return unusual

    async def get_monthly_comparison(self, months: int = 3) -> list[dict]:
        comparisons = []
        now = datetime.utcnow()
        for i in range(months):
            m = now.month - i
            y = now.year
            while m < 1:
                m += 12
                y -= 1
            month_str = f"{y}-{m:02d}"
            transactions = await self._get_month_transactions(month_str)
            total = sum(t["amount"] for t in transactions)
            by_cat: dict[str, float] = {}
            for t in transactions:
                cat = t.get("category", "Other")
                by_cat[cat] = by_cat.get(cat, 0) + t["amount"]
            comparisons.append({
                "month": month_str,
                "total": round(total, 2),
                "transaction_count": len(transactions),
                "categories": {k: round(v, 2) for k, v in sorted(by_cat.items())},
            })
        return comparisons

    async def get_top_spending_days(self, days: int = 90) -> list[dict]:
        transactions = await self._get_transactions(days)
        daily: dict[str, float] = {}
        day_details: dict[str, list] = {}
        for t in transactions:
            d = t["date"].strftime("%Y-%m-%d") if hasattr(t["date"], "strftime") else str(t["date"])[:10]
            daily[d] = daily.get(d, 0) + t["amount"]
            day_details.setdefault(d, []).append({
                "amount": t["amount"],
                "category": t.get("category", ""),
                "description": t.get("description", ""),
            })
        sorted_days = sorted(daily.items(), key=lambda x: -x[1])[:5]
        return [
            {"date": d, "total": round(v, 2), "transactions": day_details.get(d, [])}
            for d, v in sorted_days
        ]

    async def get_recurring_patterns(self) -> list[dict]:
        transactions = await self._get_transactions(90)
        desc_map: dict[str, list[float]] = {}
        cat_map: dict[str, str] = {}
        for t in transactions:
            desc = t.get("description", "").lower().strip()
            desc_map.setdefault(desc, []).append(t["amount"])
            cat_map[desc] = t.get("category", "Other")
        patterns = []
        for desc, amounts in desc_map.items():
            if len(amounts) >= 2:
                avg_amt = sum(amounts) / len(amounts)
                variance = max(amounts) - min(amounts)
                is_regular = variance < avg_amt * 0.3
                if is_regular:
                    patterns.append({
                        "description": desc.title(),
                        "category": cat_map.get(desc, "Other"),
                        "average_amount": round(avg_amt, 2),
                        "frequency": f"{len(amounts)} times in 90 days",
                        "confidence": min(round(len(amounts) / 3 * 100, 1), 95),
                    })
        return sorted(patterns, key=lambda x: -x["confidence"])
