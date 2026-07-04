import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean, stdev

from backend.database.mongo import get_db

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS = {
    "Food": ["restaurant", "grocery", "food", "dining", "lunch", "dinner", "breakfast", "cafe", "coffee", "pizza", "burger", "supermarket", "meal", "takeout", "delivery", "bakery", "snack"],
    "Transport": ["gas", "fuel", "uber", "lyft", "taxi", "bus", "train", "metro", "subway", "parking", "toll", "transport", "car", "ride", "fare", "petrol"],
    "Entertainment": ["movie", "netflix", "spotify", "concert", "game", "ticket", "cinema", "theater", "theatre", "stream", "music", "hbo", "hulu", "disney", "entertainment", "arcade", "bowling"],
    "Shopping": ["amazon", "walmart", "target", "clothing", "shirt", "shoes", "electronics", "gadget", "online", "purchase", "mall", "store", "retail", "accessory", "fashion"],
    "Utilities": ["electric", "water", "bill", "utility", "phone", "internet", "cable", "power", "gas bill", "sewage", "trash", "broadband"],
    "Medical": ["doctor", "hospital", "pharmacy", "medical", "health", "dentist", "clinic", "medicine", "prescription", "insurance", "eye", "checkup", "therapy"],
    "Rent": ["rent", "lease", "mortgage", "apartment", "housing", "property", "accommodation", "tenancy"],
    "Other": [],
}

STATUS_THRESHOLDS = {"confirmed": 0.7, "pending": 0.4}


class SmartAgent:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.thoughts: list[str] = []
        self.actions: list[str] = []
        self.observations: list[str] = []
        self.reflections: list[str] = []

    def _think(self, msg: str) -> None:
        self.thoughts.append(msg)
        logger.info("AGENT THINK: %s", msg)

    def _act(self, msg: str) -> None:
        self.actions.append(msg)
        logger.info("AGENT ACT: %s", msg)

    def _observe(self, msg: str) -> None:
        self.observations.append(msg)
        logger.info("AGENT OBSERVE: %s", msg)

    def _reflect(self, msg: str) -> None:
        self.reflections.append(msg)
        logger.info("AGENT REFLECT: %s", msg)

    def get_cycle(self) -> dict:
        return {
            "thoughts": self.thoughts[-5:],
            "actions": self.actions[-5:],
            "observations": self.observations[-5:],
            "reflections": self.reflections[-5:],
        }

    def smart_categorization(self, description: str) -> tuple[str, float, str]:
        self._think(f"Categorizing transaction: '{description}'")
        desc_lower = description.lower()
        scores: dict[str, int] = {}
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', desc_lower))
            if score > 0:
                scores[cat] = score
        if not scores:
            self._act("No keywords matched, defaulting to 'Other'")
            self._observe("Description did not match any known category keywords")
            self._reflect("Default categorization applied")
            return "Other", 0.3, "No category keywords found in description"

        best = max(scores, key=scores.get)
        total_keywords = sum(scores.values())
        runner_up = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
        confidence = min(round(scores[best] / total_keywords * 0.8 + 0.2, 2), 0.95)
        reasoning = f"Matched {scores[best]} keyword(s) in '{best}' category (next best: {runner_up} match(es))"

        self._act(f"Assigned category '{best}' with confidence {confidence}")
        self._observe(reasoning)
        self._reflect(f"Categorization complete: {best} (confidence: {confidence})")
        return best, confidence, reasoning

    async def analyze_spending_patterns(self) -> dict:
        self._think("Analyzing spending patterns from transaction history")
        db = await get_db()
        since = datetime.utcnow() - timedelta(days=90)
        cursor = db["transactions"].find({"user_id": self.user_id, "date": {"$gte": since}}).sort("date", 1)
        transactions = await cursor.to_list(length=None)

        if not transactions:
            self._observe("No transactions found in the last 90 days")
            self._reflect("Insufficient data for pattern analysis")
            return {"insights": [], "cycle": self.get_cycle()}

        monthly: dict[str, float] = {}
        daily_counts: dict[str, int] = {}
        category_totals: dict[str, float] = {}
        for t in transactions:
            d = t["date"]
            m = d.strftime("%Y-%m") if hasattr(d, "strftime") else str(d)[:7]
            monthly[m] = monthly.get(m, 0) + t["amount"]
            cat = t.get("category", "Other")
            category_totals[cat] = category_totals.get(cat, 0) + t["amount"]

        insights = []
        months = sorted(monthly.keys())
        if len(months) >= 2:
            first, last = monthly[months[0]], monthly[months[-1]]
            change = round((last - first) / max(first, 0.01) * 100, 1)
            direction = "increased" if change > 0 else "decreased"
            insights.append({
                "type": "spending_trend",
                "message": f"Total spending {direction} by {abs(change)}% over {len(months)} months",
                "confidence": min(abs(change) / 2, 95),
            })
            self._observe(f"Monthly trend: {direction} {abs(change)}%")

        top_cat = max(category_totals, key=category_totals.get)
        cat_pct = round(category_totals[top_cat] / sum(category_totals.values()) * 100, 1)
        insights.append({
            "type": "top_category",
            "message": f"Top spending category is '{top_cat}' at {cat_pct}% of total",
            "confidence": 85,
        })

        amounts = [t["amount"] for t in transactions]
        if len(amounts) > 1:
            avg_amt = mean(amounts)
            max_amt = max(amounts)
            if max_amt > avg_amt * 5:
                insights.append({
                    "type": "large_transactions",
                    "message": f"Detected unusually large transactions (max ${max_amt:.2f} vs avg ${avg_amt:.2f})",
                    "confidence": 80,
                })

        self._act(f"Generated {len(insights)} pattern insights from {len(transactions)} transactions")
        self._reflect("Spending pattern analysis complete")
        return {"insights": insights, "cycle": self.get_cycle()}

    async def suggest_improvements(self) -> list[dict]:
        self._think("Analyzing spending to suggest improvement opportunities")
        db = await get_db()
        since = datetime.utcnow() - timedelta(days=60)
        cursor = db["transactions"].find({"user_id": self.user_id, "date": {"$gte": since}})
        transactions = await cursor.to_list(length=None)

        suggestions = []
        if not transactions:
            return suggestions

        cat_total: dict[str, float] = {}
        for t in transactions:
            cat = t.get("category", "Other")
            cat_total[cat] = cat_total.get(cat, 0) + t["amount"]

        total = sum(cat_total.values())
        for cat, amt in sorted(cat_total.items(), key=lambda x: -x[1]):
            pct = amt / total * 100
            if pct > 30 and cat not in ("Rent", "Medical"):
                suggestions.append({
                    "category": cat,
                    "current_spend": round(amt, 2),
                    "percentage": round(pct, 1),
                    "suggestion": f"Consider reducing '{cat}' spending ({pct:.0f}% of total). Target: {round(amt * 0.8, 2)}",
                    "potential_savings": round(amt * 0.2, 2),
                })

        self._act(f"Generated {len(suggestions)} improvement suggestions")
        self._reflect("Improvement analysis complete")
        return suggestions

    async def risk_assessment(self, amount: float, category: str) -> dict:
        self._think(f"Assessing risk for ${amount:.2f} in '{category}'")
        risk_score = 0
        risk_factors = []

        if amount > 5000:
            risk_score += 40
            risk_factors.append("High-value transaction (>$5000)")

        if amount > 10000:
            risk_score += 20
            risk_factors.append("Very high value (>$10000)")

        db = await get_db()
        since = datetime.utcnow() - timedelta(days=90)
        cursor = db["transactions"].find({"user_id": self.user_id, "category": category, "date": {"$gte": since}})
        similar = await cursor.to_list(length=None)
        if similar:
            avg = mean(t["amount"] for t in similar)
            if amount > avg * 3:
                risk_score += 30
                risk_factors.append(f"Amount {amount/avg:.1f}x higher than average for '{category}'")

        if category in ("Entertainment", "Shopping") and amount > 2000:
            risk_score += 20
            risk_factors.append(f"High discretionary spending in '{category}'")

        level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high"
        self._act(f"Risk score: {risk_score}/100, Level: {level}")
        self._reflect("Risk assessment complete")

        return {
            "risk_score": risk_score,
            "risk_level": level,
            "risk_factors": risk_factors,
            "recommended_action": "review" if risk_score >= 30 else "approve",
        }

    async def generate_insights(self, period: int = 30) -> dict:
        self._think(f"Generating natural language insights for last {period} days")
        db = await get_db()
        since = datetime.utcnow() - timedelta(days=period)
        cursor = db["transactions"].find({"user_id": self.user_id, "date": {"$gte": since}}).sort("date", 1)
        transactions = await cursor.to_list(length=None)

        if not transactions:
            return {
                "summary": "No transactions found in the analyzed period.",
                "insights": [],
                "cycle": self.get_cycle(),
            }

        total = sum(t["amount"] for t in transactions)
        count = len(transactions)
        avg_amount = total / count
        by_category: dict[str, float] = {}
        for t in transactions:
            cat = t.get("category", "Other")
            by_category[cat] = by_category.get(cat, 0) + t["amount"]
        top_cat = max(by_category, key=by_category.get)
        dates = [t["date"] for t in transactions]
        date_range = f"{dates[0].strftime('%b %d')} - {dates[-1].strftime('%b %d, %Y')}" if hasattr(dates[0], 'strftime') else f"{period} days"

        self._observe(f"{count} transactions, ${total:.2f} total, avg ${avg_amount:.2f}")

        lines = []
        lines.append(f"Over the {period}-day period ({date_range}), you made {count} transactions totaling ${total:.2f}.")
        lines.append(f"Average transaction: ${avg_amount:.2f}.")
        lines.append(f"Your top spending category is '{top_cat}' at ${by_category[top_cat]:.2f}.")

        top_pct = by_category[top_cat] / total * 100
        if top_pct > 30:
            lines.append(f"'{top_cat}' accounts for {top_pct:.0f}% of total spending.")
        if avg_amount > 200:
            lines.append("Your average transaction amount is relatively high. Consider reviewing individual expenses.")

        self._reflect("Natural language insights generated")
        return {
            "summary": " ".join(lines),
            "insights": [
                {"type": "total", "value": round(total, 2), "label": f"Total spent ({period} days)"},
                {"type": "count", "value": count, "label": "Transactions"},
                {"type": "average", "value": round(avg_amount, 2), "label": "Average transaction"},
                {"type": "top_category", "value": top_cat, "label": f"${by_category[top_cat]:.2f}"},
            ],
            "cycle": self.get_cycle(),
        }
