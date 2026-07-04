import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean, stdev
from typing import Any, Optional

from backend.database.mongo import get_db

logger = logging.getLogger(__name__)

CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Utilities", "Medical", "Rent", "Other"]


class ForecasterAgent:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self._thoughts: list[str] = []
        self._actions: list[str] = []
        self._observations: list[str] = []
        self._reflections: list[str] = []

    def _think(self, message: str) -> None:
        self._thoughts.append(message)
        logger.info("FORECAST THINK: %s", message)

    def _act(self, message: str) -> None:
        self._actions.append(message)
        logger.info("FORECAST ACT: %s", message)

    def _observe(self, message: str) -> None:
        self._observations.append(message)
        logger.info("FORECAST OBSERVE: %s", message)

    def _reflect(self, message: str) -> None:
        self._reflections.append(message)
        logger.info("FORECAST REFLECT: %s", message)

    def get_cycle(self) -> dict:
        return {
            "thoughts": self._thoughts,
            "actions": self._actions,
            "observations": self._observations,
            "reflections": self._reflections,
        }

    async def _get_history(self, months: int = 3) -> list[dict]:
        db = await get_db()
        since = datetime.utcnow() - timedelta(days=months * 31)
        cursor = db["transactions"].find({
            "user_id": self.user_id,
            "date": {"$gte": since},
        }).sort("date", 1)
        return await cursor.to_list(length=None)

    async def _monthly_totals(self, transactions: list[dict]) -> dict[str, dict[str, float]]:
        monthly: dict[str, dict[str, float]] = {}
        for t in transactions:
            d = t["date"]
            m = d.strftime("%Y-%m") if hasattr(d, "strftime") else str(d)[:7]
            monthly.setdefault(m, {})
            cat = t.get("category", "Other")
            monthly[m][cat] = monthly[m].get(cat, 0) + t["amount"]
        return monthly

    async def forecast_next_month(self, history_months: int = 3) -> dict:
        self._think(f"Analyzing historical spending over {history_months} months to forecast next month")
        transactions = await self._get_history(history_months)
        if not transactions:
            self._observe("No transaction history available for forecasting")
            self._reflect("Cannot generate forecast without data")
            return {"forecast": {}, "confidence": 0, "risk_factors": ["No data"], "cycle": self.get_cycle()}

        monthly_data = await self._monthly_totals(transactions)
        months_list = sorted(monthly_data.keys())
        self._observe(f"Found data for {len(months_list)} months: {months_list}")

        if len(months_list) < 2:
            single_month = months_list[0]
            forecast = monthly_data[single_month]
            self._reflect("Only one month of data; using current spending as forecast")
            return {
                "forecast": {cat: round(amt, 2) for cat, amt in forecast.items()},
                "total": round(sum(forecast.values()), 2),
                "confidence": 30,
                "risk_factors": ["Limited historical data"],
                "cycle": self.get_cycle(),
            }

        forecast: dict[str, float] = {}
        for cat in CATEGORIES:
            values = []
            for m in months_list:
                values.append(monthly_data[m].get(cat, 0))
            if len(values) >= 2:
                trend = (values[-1] - values[0]) / max(len(values) - 1, 1)
                predicted = values[-1] + trend
                if predicted < 0:
                    predicted = mean(values)
            else:
                predicted = values[0] if values else 0
            forecast[cat] = max(round(predicted, 2), 0)

        self._act("Calculated linear trend for each category")

        all_values = [sum(monthly_data[m].values()) for m in months_list]
        if len(all_values) >= 2:
            volatility = round(stdev(all_values) / mean(all_values) * 100, 1) if mean(all_values) > 0 else 0
        else:
            volatility = 0
        confidence = max(30, min(95, round(100 - volatility)))
        self._observe(f"Volatility: {volatility}%, Confidence: {confidence}%")

        risk_factors = []
        if volatility > 50:
            risk_factors.append("High spending volatility")
        if max(forecast.values()) > 0 and max(forecast.values()) / (sum(forecast.values()) / max(len([v for v in forecast.values() if v > 0]), 1)) > 3:
            risk_factors.append("Spending concentrated in one category")

        total_forecast = round(sum(forecast.values()), 2)
        self._reflect(f"Forecast generated: ${total_forecast} total with {confidence}% confidence")

        return {
            "forecast": forecast,
            "total": total_forecast,
            "confidence": confidence,
            "volatility": volatility,
            "risk_factors": risk_factors,
            "cycle": self.get_cycle(),
        }

    async def forecast_by_category(self, category: str, months: int = 3) -> dict:
        self._think(f"Forecasting category '{category}' over {months} months")
        transactions = await self._get_history(months)
        cat_txns = [t for t in transactions if t.get("category") == category]
        if not cat_txns:
            self._observe(f"No transactions found for category '{category}'")
            self._reflect("Cannot forecast category with no data")
            return {"category": category, "forecast": 0, "confidence": 0, "cycle": self.get_cycle()}

        monthly: dict[str, float] = {}
        for t in cat_txns:
            d = t["date"]
            m = d.strftime("%Y-%m") if hasattr(d, "strftime") else str(d)[:7]
            monthly[m] = monthly.get(m, 0) + t["amount"]
        months_list = sorted(monthly.keys())

        if len(months_list) < 2:
            self._reflect("Only one month of data for this category")
            return {"category": category, "forecast": round(monthly[months_list[0]], 2), "confidence": 30, "cycle": self.get_cycle()}

        values = [monthly[m] for m in months_list]
        trend = (values[-1] - values[0]) / (len(values) - 1)
        predicted = max(values[-1] + trend, 0)
        vol = round(stdev(values) / mean(values) * 100, 1) if mean(values) > 0 else 0
        conf = max(30, min(95, round(100 - vol)))

        self._act(f"Trend: ${trend:.2f}/month, Volatility: {vol}%")
        self._reflect(f"Category '{category}' forecast: ${predicted:.2f}")

        return {
            "category": category,
            "forecast": round(predicted, 2),
            "confidence": conf,
            "monthly_totals": {m: round(v, 2) for m, v in monthly.items()},
            "trend": round(trend, 2),
            "volatility": vol,
            "cycle": self.get_cycle(),
        }

    async def predict_total_spending(self, days: int = 30) -> dict:
        self._think(f"Predicting total spending for next {days} days")
        transactions = await self._get_history(3)
        if not transactions:
            return {"predicted_total": 0, "daily_average": 0, "confidence": 0, "cycle": self.get_cycle()}

        total_days = 90
        daily_avg = sum(t["amount"] for t in transactions) / total_days
        current_month = await self._get_history(1)
        current_avg = sum(t["amount"] for t in current_month) / max(len(current_month), 1)
        weight = 0.6
        blended = daily_avg * (1 - weight) + current_avg * weight
        predicted = round(blended * days, 2)

        self._act(f"Daily avg (3mo): ${daily_avg:.2f}, Current avg: ${current_avg:.2f}, Blended: ${blended:.2f}")
        self._observe(f"Historical daily average across {len(transactions)} transactions")
        self._reflect(f"Predicted {days}-day total: ${predicted}")

        amounts = [t["amount"] for t in transactions]
        vol = round(stdev(amounts) / mean(amounts) * 100, 1) if mean(amounts) > 0 else 50
        conf = max(30, min(95, round(100 - vol / 2)))

        return {
            "predicted_total": predicted,
            "daily_average": round(blended, 2),
            "days": days,
            "confidence": conf,
            "cycle": self.get_cycle(),
        }

    async def identify_spending_trends(self) -> dict:
        self._think("Analyzing spending trends across all categories")
        transactions = await self._get_history(3)
        if not transactions:
            return {"trends": [], "cycle": self.get_cycle()}

        monthly = await self._monthly_totals(transactions)
        months_list = sorted(monthly.keys())
        if len(months_list) < 2:
            return {"trends": [], "message": "Need at least 2 months of data", "cycle": self.get_cycle()}

        trends = []
        for cat in CATEGORIES:
            values = [monthly[m].get(cat, 0) for m in months_list]
            if max(values) == 0:
                continue
            first, last = values[0], values[-1]
            pct_change = round((last - first) / max(first, 0.01) * 100, 1)
            if abs(pct_change) > 5:
                direction = "uptrend" if pct_change > 0 else "downtrend"
            else:
                direction = "stable"
            vol = round(stdev(values) / mean(values) * 100, 1) if mean(values) > 0 else 0
            trends.append({
                "category": cat,
                "direction": direction,
                "percent_change": pct_change,
                "volatility": vol,
                "current_monthly": round(last, 2),
            })

        self._act(f"Analyzed {len(trends)} categories for trends")
        self._reflect("Trend analysis complete")

        return {"trends": sorted(trends, key=lambda x: -abs(x["percent_change"])), "cycle": self.get_cycle()}

    async def suggest_budget_adjustments(self) -> dict:
        self._think("Analyzing spending patterns to suggest optimal budget adjustments")
        cycle = self.get_cycle()
        try:
            forecast_data = await self.forecast_next_month(3)
        except Exception:
            return {"suggestions": [], "reasoning": "Insufficient data", "cycle": cycle}

        forecast = forecast_data.get("forecast", {})
        if not forecast:
            return {"suggestions": [], "reasoning": "Cannot generate forecast with available data", "cycle": cycle}

        db = await get_db()
        month = datetime.utcnow().strftime("%Y-%m")
        budget_doc = await db["budgets"].find_one({"user_id": self.user_id, "month": month})
        current_budget = budget_doc["budgets"] if budget_doc else {}

        suggestions = []
        for cat in CATEGORIES:
            predicted = forecast.get(cat, 0)
            current = current_budget.get(cat, 0)
            if predicted > 0 and current > 0:
                diff = round(predicted - current, 2)
                pct_diff = round(diff / current * 100, 1)
                if abs(pct_diff) > 10:
                    action = "increase" if diff > 0 else "decrease"
                    suggestions.append({
                        "category": cat,
                        "current_budget": current,
                        "suggested_budget": round(predicted * 1.1, 2),
                        "difference": abs(diff),
                        "percent_change": pct_diff,
                        "action": action,
                        "reason": f"Predicted spending ({action}s by {abs(pct_diff)}%) based on trend",
                    })
            elif predicted > 0 and current == 0:
                suggestions.append({
                    "category": cat,
                    "current_budget": 0,
                    "suggested_budget": round(predicted * 1.1, 2),
                    "difference": round(predicted * 1.1, 2),
                    "percent_change": 100,
                    "action": "create",
                    "reason": f"New budget needed - predicted ${predicted:.2f} spending",
                })

        reasoning = (
            f"Analyzed {len(forecast)} categories across forecast and current budget. "
            f"Found {len(suggestions)} adjustment opportunities."
        )
        self._reflect(reasoning)

        return {
            "suggestions": suggestions,
            "reasoning": reasoning,
            "forecast_confidence": forecast_data.get("confidence", 0),
            "cycle": cycle,
        }
