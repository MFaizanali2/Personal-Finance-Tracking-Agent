import logging
from datetime import date, datetime

from backend.agent.agent import BaseAgent
from database import get_user_budgets, get_budget_by_id, get_budget_spent_percentage, get_budget_remaining, check_budget_alerts

logger = logging.getLogger(__name__)


class BudgetMonitorAgent(BaseAgent):
    """ReACT-based agent that monitors budgets, checks thresholds, and provides spending insights."""

    def __init__(self, gemini_api_key: str = ""):
        super().__init__(name="BudgetMonitor", gemini_api_key=gemini_api_key)
        self._register_tools()

    def _register_tools(self):
        self.register_tool(
            name="check_status",
            func=self.check_budget_status,
            description="Checks current status of all budgets for a user in a given month",
        )
        self.register_tool(
            name="analyze_velocity",
            func=self.analyze_spending_velocity,
            description="Analyzes how fast user is spending relative to their budget limit",
        )
        self.register_tool(
            name="generate_alerts",
            func=self.generate_budget_alerts,
            description="Generates alerts for budgets approaching or exceeding limits",
        )
        self.register_tool(
            name="suggest_adjustments",
            func=self.suggest_budget_adjustments,
            description="Suggests budget limit adjustments based on spending patterns",
        )

    def check_budget_status(self, user_id: str, month: str) -> dict:
        """Check budget status for a user in a given month."""
        raw_budgets = get_user_budgets(user_id, month)
        budget_list = []
        total_limit = 0.0
        total_spent = 0.0

        for b in raw_budgets:
            limit = b.get("monthly_limit", 0)
            spent = b.get("spent_so_far", 0)
            pct = round(spent / limit * 100, 1) if limit > 0 else 0
            remaining = round(limit - spent, 2)
            status_label = "exceeded" if pct >= 100 else "warning" if pct >= 80 else "ok"
            total_limit += limit
            total_spent += spent
            budget_list.append({
                "budget_id": b.get("budget_id", ""),
                "category": b.get("category", "Unknown"),
                "limit": limit,
                "spent": spent,
                "percentage": pct,
                "status": status_label,
                "remaining": remaining,
            })

        summary = {
            "total_budgets": len(budget_list),
            "total_limit": round(total_limit, 2),
            "total_spent": round(total_spent, 2),
            "total_remaining": round(total_limit - total_spent, 2),
            "overall_percentage": round(total_spent / total_limit * 100, 1) if total_limit > 0 else 0,
        }

        print(f"[STATUS] {summary['total_budgets']} budgets checked: {summary['overall_percentage']}% spent")
        return {
            "user_id": user_id,
            "month": month,
            "budgets": budget_list,
            "summary": summary,
            "checked_at": datetime.now().isoformat(),
        }

    def analyze_spending_velocity(self, spent: float, limit: float, days_elapsed: int, days_in_month: int = 30) -> dict:
        """Analyze how fast money is being spent relative to budget."""
        if days_elapsed <= 0:
            return {"error": "Cannot calculate velocity on day 0"}
        daily_average = spent / days_elapsed
        remaining_days = days_in_month - days_elapsed
        projected_final = spent + (daily_average * remaining_days)
        will_exceed = projected_final > limit
        days_until_exhausted = int(limit / daily_average) if daily_average > 0 else days_in_month
        daily_budget = limit / days_in_month

        if will_exceed:
            reduction = (daily_average - daily_budget) / daily_average * 100
            recommendation = f"Will exceed budget. Reduce daily spending by {reduction:.1f}%"
        elif daily_average > daily_budget * 0.9:
            recommendation = "Spending close to limit. Be cautious."
        else:
            recommendation = "On track. Continue monitoring."

        velocity = {
            "spent_so_far": spent,
            "limit": limit,
            "days_elapsed": days_elapsed,
            "daily_average": round(daily_average, 2),
            "projected_final_amount": round(projected_final, 2),
            "will_exceed_budget": will_exceed,
            "days_until_exhausted": days_until_exhausted,
            "days_remaining": remaining_days,
            "recommendation": recommendation,
        }

        print(f"[VELOCITY] ${daily_average:.2f}/day | Projected: ${projected_final:.0f} | Exceed: {will_exceed}")
        return velocity

    def generate_budget_alerts(self, budgets: list) -> dict:
        """Generate alerts for budgets at 80% and 100% thresholds."""
        critical, warning, ok = [], [], []

        for b in budgets:
            spent = b.get("spent", 0)
            limit_val = b.get("limit", 1)
            pct = (spent / limit_val) * 100 if limit_val > 0 else 0
            alert = {
                "category": b.get("category", "Unknown"),
                "spent": spent,
                "limit": limit_val,
                "percentage": round(pct, 1),
                "amount_over": max(0, spent - limit_val),
            }
            if pct >= 100:
                critical.append(alert)
            elif pct >= 80:
                warning.append(alert)
            else:
                ok.append(alert)

        alerts = {
            "critical_alerts": critical,
            "warning_alerts": warning,
            "ok_budgets": ok,
            "total_alerts": len(critical) + len(warning),
            "alert_priority": "critical" if critical else ("warning" if warning else "ok"),
            "generated_at": datetime.now().isoformat(),
        }

        if alerts["total_alerts"] > 0:
            print(f"[ALERTS] {alerts['total_alerts']} alert(s): {len(critical)} critical, {len(warning)} warning")
        return alerts

    def suggest_budget_adjustments(self, spending_history: list, current_budgets: list) -> dict:
        """Suggest budget limit adjustments based on historical spending."""
        adjustments = []
        for budget in current_budgets:
            category = budget.get("category")
            current_limit = budget.get("limit", 0)
            category_spending = [s.get("amount", 0) for s in spending_history if s.get("category") == category]
            if not category_spending:
                continue
            avg_spending = sum(category_spending) / len(category_spending)
            spent_pct = (avg_spending / current_limit) * 100 if current_limit > 0 else 0
            if spent_pct > 90:
                suggested = avg_spending * 1.15
                reason = f"Consistently spending {spent_pct:.0f}% of budget"
                confidence = 85.0
            elif spent_pct < 50:
                suggested = avg_spending * 1.3
                reason = f"Only using {spent_pct:.0f}% of budget"
                confidence = 70.0
            else:
                suggested = current_limit
                reason = "Budget is well-balanced"
                confidence = 90.0
            if suggested != current_limit:
                adjustments.append({
                    "category": category,
                    "current_limit": current_limit,
                    "suggested_limit": round(suggested, 2),
                    "reason": reason,
                    "confidence_percentage": confidence,
                })

        print(f"[ADJUSTMENTS] {len(adjustments)} suggestion(s)")
        return {"adjustments": adjustments, "recommendation_date": datetime.now().isoformat()}

    def process(self, user_id: str, month: str, budgets: list, spending_history: list) -> dict:
        """Run the full budget monitoring ReACT loop."""
        print(f"\n{'='*50}")
        print(f"[PROCESS] BudgetMonitor checking for user '{user_id}' in {month}")
        print(f"{'='*50}")

        self.memory.clear()
        self.thinking_history.clear()

        print("\n--- STEP 1: Check Budget Status ---")
        status = self.check_budget_status(user_id, month)

        print("\n--- STEP 2: Analyze Spending Velocity ---")
        today = date.today()
        days_elapsed = today.day
        velocity_analysis = {}
        for b in status.get("budgets", []):
            vel = self.analyze_spending_velocity(b.get("spent", 0), b.get("limit", 0), days_elapsed)
            velocity_analysis[b.get("category")] = vel

        print("\n--- STEP 3: Generate Alerts ---")
        alerts = self.generate_budget_alerts(status.get("budgets", []))

        print("\n--- STEP 4: Suggest Adjustments ---")
        adjustments = self.suggest_budget_adjustments(spending_history, budgets)

        report = {
            "user_id": user_id,
            "month": month,
            "budget_status": status,
            "alerts": alerts,
            "spending_velocity": velocity_analysis,
            "suggested_adjustments": adjustments,
            "report_generated": datetime.now().isoformat(),
        }

        self.memory.append(report)
        print(f"\n{'='*50}")
        print(f"[DONE] Monitoring complete for user '{user_id}'")
        print(f"{'='*50}")

        return report


def process_budget_monitor(user_id: str, month: str, budgets: list, spending_history: list) -> dict:
    """Convenience function: create agent, run process, return report."""
    agent = BudgetMonitorAgent()
    return agent.process(user_id, month, budgets, spending_history)
