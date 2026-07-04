import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from backend.database.mongo import get_db

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"critical": 3, "warning": 2, "info": 1}


class AlertSystem:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    async def _get_transactions(self, days: int = 30) -> list[dict]:
        db = await get_db()
        since = datetime.utcnow() - timedelta(days=days)
        cursor = db["transactions"].find({"user_id": self.user_id, "date": {"$gte": since}})
        return await cursor.to_list(length=None)

    async def check_budget_alerts(self) -> list[dict]:
        db = await get_db()
        month = datetime.utcnow().strftime("%Y-%m")
        budget_doc = await db["budgets"].find_one({"user_id": self.user_id, "month": month})
        if not budget_doc:
            return []
        budget = budget_doc["budgets"]
        transactions = await self._get_transactions(30)
        actuals: dict[str, float] = {}
        for t in transactions:
            cat = t.get("category", "Other")
            actuals[cat] = actuals.get(cat, 0) + t["amount"]
        alerts = []
        for cat, b in budget.items():
            if b <= 0:
                continue
            actual = actuals.get(cat, 0)
            pct = actual / b * 100
            if pct >= 90:
                severity = "critical"
                message = f"Category '{cat}' has used {pct:.0f}% of budget (${actual:.2f}/${b:.2f})"
            elif pct >= 75:
                severity = "warning"
                message = f"Category '{cat}' has used {pct:.0f}% of budget (${actual:.2f}/${b:.2f})"
            else:
                continue
            alerts.append({
                "type": "budget_alert",
                "severity": severity,
                "category": cat,
                "message": message,
                "budgeted": b,
                "actual": round(actual, 2),
                "percentage_used": round(pct, 1),
            })
        return alerts

    async def check_unusual_spending(self) -> list[dict]:
        transactions = await self._get_transactions(30)
        if not transactions:
            return []
        amounts = [t["amount"] for t in transactions]
        avg_amount = sum(amounts) / len(amounts)
        threshold = avg_amount * 2
        alerts = []
        for t in transactions:
            if t["amount"] > threshold:
                d = t["date"].strftime("%Y-%m-%d") if hasattr(t["date"], "strftime") else ""
                alerts.append({
                    "type": "unusual_spending",
                    "severity": "warning",
                    "transaction_id": str(t["_id"]),
                    "amount": t["amount"],
                    "category": t.get("category", ""),
                    "description": t.get("description", ""),
                    "date": d,
                    "message": f"Unusual spending: ${t['amount']:.2f} in '{t.get('category', '')}' ({t.get('description', '')})",
                })
        return alerts

    async def check_trend_changes(self) -> list[dict]:
        db = await get_db()
        now = datetime.utcnow()
        recent = now - timedelta(days=7)
        prev = now - timedelta(days=14)
        cursor_recent = db["transactions"].find({"user_id": self.user_id, "date": {"$gte": recent}})
        recent_txns = await cursor_recent.to_list(length=None)
        cursor_prev = db["transactions"].find({"user_id": self.user_id, "date": {"$gte": prev, "$lt": recent}})
        prev_txns = await cursor_prev.to_list(length=None)
        recent_total = sum(t["amount"] for t in recent_txns) / 7
        prev_total = sum(t["amount"] for t in prev_txns) / 7
        alerts = []
        if prev_total > 0:
            change = (recent_total - prev_total) / prev_total * 100
            if abs(change) > 30:
                direction = "increasing" if change > 0 else "decreasing"
                alerts.append({
                    "type": "trend_change",
                    "severity": "warning",
                    "message": f"Spending trend is {direction} rapidly ({abs(change):.0f}% change week-over-week)",
                    "percent_change": round(change, 1),
                    "weekly_avg_previous": round(prev_total, 2),
                    "weekly_avg_recent": round(recent_total, 2),
                })
        return alerts

    async def check_warning_alerts(self) -> list[dict]:
        db = await get_db()
        month = datetime.utcnow().strftime("%Y-%m")
        budget_doc = await db["budgets"].find_one({"user_id": self.user_id, "month": month})
        if not budget_doc:
            return []
        total_budget = budget_doc.get("total_budget", sum(budget_doc["budgets"].values()))
        now = datetime.utcnow()
        days_in_month = 30
        day_of_month = now.day
        transactions = await self._get_transactions(day_of_month)
        total_spent = sum(t["amount"] for t in transactions)
        if total_budget > 0 and day_of_month > 0:
            projected = total_spent / day_of_month * days_in_month
            if projected > total_budget:
                over_pct = round((projected - total_budget) / total_budget * 100, 1)
                return [{
                    "type": "budget_warning",
                    "severity": "critical",
                    "message": f"On pace to exceed monthly budget by {over_pct}% (projected: ${projected:.2f}, budget: ${total_budget:.2f})",
                    "total_budget": total_budget,
                    "spent_so_far": round(total_spent, 2),
                    "projected_total": round(projected, 2),
                    "day_of_month": day_of_month,
                }]
        return []

    async def check_pace_alerts(self) -> list[dict]:
        db = await get_db()
        month = datetime.utcnow().strftime("%Y-%m")
        budget_doc = await db["budgets"].find_one({"user_id": self.user_id, "month": month})
        if not budget_doc:
            return []
        budgets = budget_doc["budgets"]
        now = datetime.utcnow()
        day_of_month = now.day
        if day_of_month == 0:
            return []
        factor = day_of_month / 30
        transactions = await self._get_transactions(day_of_month)
        actuals: dict[str, float] = {}
        for t in transactions:
            cat = t.get("category", "Other")
            actuals[cat] = actuals.get(cat, 0) + t["amount"]
        alerts = []
        for cat, budget_amt in budgets.items():
            if budget_amt <= 0:
                continue
            actual = actuals.get(cat, 0)
            expected = budget_amt * factor
            if actual > expected * 1.3:
                alerts.append({
                    "type": "pace_alert",
                    "severity": "warning",
                    "category": cat,
                    "message": f"'{cat}' spending is ahead of pace (${actual:.2f} spent vs ${expected:.2f} expected)",
                    "budgeted": budget_amt,
                    "actual": round(actual, 2),
                    "expected": round(expected, 2),
                })
        return alerts

    async def check_goal_alerts(self) -> list[dict]:
        db = await get_db()
        cursor = db["goals"].find({"user_id": self.user_id, "status": "active"})
        goals = await cursor.to_list(length=None)
        alerts = []
        for g in goals:
            target = g["target_amount"]
            current = g.get("current_amount", 0)
            remaining = target - current
            deadline = g["deadline"] if isinstance(g["deadline"], datetime) else datetime.strptime(str(g["deadline"])[:10], "%Y-%m-%d")
            days_left = (deadline - datetime.utcnow()).days
            months_left = max(days_left / 30, 0.5)
            monthly = g.get("monthly_contribution", 0)
            needed = round(remaining / months_left, 2) if remaining > 0 else 0

            pct = round(current / target * 100, 1) if target > 0 else 0
            if days_left < 0:
                alerts.append({"type": "goal_overdue", "severity": "critical", "goal_id": str(g["_id"]), "name": g["name"], "message": f"Goal '{g['name']}' is overdue ({abs(days_left)} days past deadline)"})
            elif days_left < 30 and pct < 90:
                alerts.append({"type": "goal_at_risk", "severity": "critical", "goal_id": str(g["_id"]), "name": g["name"], "message": f"Goal '{g['name']}' deadline approaching ({days_left} days left, only {pct}% saved)"})
            elif monthly > 0 and needed > monthly * 1.5:
                alerts.append({"type": "goal_underfunded", "severity": "warning", "goal_id": str(g["_id"]), "name": g["name"], "message": f"Goal '{g['name']}' needs ${needed:.0f}/mo but saving ${monthly:.0f}/mo"})
            if current >= target and g.get("status") == "active":
                alerts.append({"type": "goal_achieved", "severity": "info", "goal_id": str(g["_id"]), "name": g["name"], "message": f"Goal '{g['name']}' achieved! 🎉"})
                await db["goals"].update_one({"_id": g["_id"]}, {"$set": {"status": "completed", "updated_at": datetime.utcnow()}})
        return alerts

    async def generate_alerts(self) -> list[dict]:
        all_alerts = []
        for check in [self.check_budget_alerts, self.check_unusual_spending,
                       self.check_trend_changes, self.check_warning_alerts,
                       self.check_pace_alerts, self.check_goal_alerts]:
            try:
                result = await check()
                all_alerts.extend(result)
            except Exception as e:
                logger.error("Alert check failed: %s", e)
        all_alerts.sort(key=lambda a: SEVERITY_ORDER.get(a.get("severity", "info"), 0), reverse=True)
        return all_alerts

    async def save_alerts(self, alerts: list[dict]) -> None:
        if not alerts:
            return
        db = await get_db()
        now = datetime.utcnow()
        for alert in alerts:
            alert["user_id"] = self.user_id
            alert["created_at"] = now
            alert["dismissed"] = False
        await db["alerts"].insert_many(alerts)
        logger.info("Saved %d alerts to database", len(alerts))

    async def get_current_alerts(self) -> list[dict]:
        alerts = await self.generate_alerts()
        await self.save_alerts(alerts)
        return alerts

    async def get_alert_history(self) -> list[dict]:
        db = await get_db()
        cursor = db["alerts"].find({"user_id": self.user_id}).sort("created_at", -1).limit(100)
        results = await cursor.to_list(length=None)
        for r in results:
            r["_id"] = str(r["_id"])
            if isinstance(r.get("created_at"), datetime):
                r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return results

    async def dismiss_alert(self, alert_id: str) -> bool:
        from bson.objectid import ObjectId
        db = await get_db()
        result = await db["alerts"].update_one(
            {"_id": ObjectId(alert_id), "user_id": self.user_id},
            {"$set": {"dismissed": True, "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def get_alert_summary(self) -> dict:
        alerts = await self.generate_alerts()
        critical = sum(1 for a in alerts if a.get("severity") == "critical")
        warning = sum(1 for a in alerts if a.get("severity") == "warning")
        types: dict[str, int] = {}
        for a in alerts:
            t = a.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
        return {"total": len(alerts), "critical": critical, "warning": warning, "by_type": types}
