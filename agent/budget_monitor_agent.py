"""
BudgetMonitorAgent — ReACT-based agent that monitors budget thresholds,
analyzes spending velocity, generates alerts, and suggests reallocations.
"""
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from memory import AgentMemory

logger = logging.getLogger(__name__)

TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {}


def tool(name: Optional[str] = None) -> Callable:
    def decorator(fn: Callable) -> Callable:
        tool_name = name or fn.__name__
        TOOL_REGISTRY[tool_name] = fn
        @wraps(fn)
        def wrapper(*args, **kwargs):
            logger.info("[TOOL] %s called with args=%s kwargs=%s", tool_name, args, kwargs)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@tool("check_budget_status")
def check_budget_status(budget_id: str, category: str = "", spent: float = 0, limit: float = 0) -> dict:
    spent_pct = round(spent / limit * 100, 1) if limit > 0 else 0
    remaining = max(limit - spent, 0)

    if spent_pct >= 100:
        status = "exceeded"
    elif spent_pct >= 80:
        status = "critical"
    elif spent_pct >= 50:
        status = "warning"
    else:
        status = "ok"

    logger.info("check_budget_status[%s]: %.1f%% spent (%s)", category or budget_id, spent_pct, status)
    return {
        "budget_id": budget_id,
        "category": category,
        "spent_percentage": spent_pct,
        "remaining": round(remaining, 2),
        "spent": round(spent, 2),
        "limit": round(limit, 2),
        "status": status,
    }


@tool("analyze_spending_velocity")
def analyze_spending_velocity(category: str, days_into_month: int, spent: float, limit: float) -> dict:
    days_into_month = max(days_into_month, 1)
    daily_avg = round(spent / days_into_month, 2)
    days_in_month = 30
    remaining_days = max(days_in_month - days_into_month, 1)
    projected = round(daily_avg * days_in_month, 2)
    will_exceed = projected > limit

    pace = "over" if daily_avg * days_in_month > limit else "under" if daily_avg * days_in_month < limit * 0.8 else "at"

    remaining_budget = max(limit - spent, 0)
    allowed_daily = round(remaining_budget / remaining_days, 2) if remaining_days > 0 else 0

    logger.info("analyze_spending_velocity[%s]: daily=$%.2f, projected=$%.2f (pace=%s)", category, daily_avg, projected, pace)
    return {
        "category": category,
        "daily_avg": daily_avg,
        "projected_final": projected,
        "will_exceed": will_exceed,
        "pace": pace,
        "allowed_daily_remaining": allowed_daily,
        "days_remaining": remaining_days,
        "remaining_budget": round(remaining_budget, 2),
    }


@tool("generate_budget_alert")
def generate_budget_alert(category: str, spent_pct: float, budget_limit: float, spent: float = 0) -> dict:
    if spent_pct >= 100:
        severity = "critical"
        message = f"{category} budget of ${budget_limit:.2f} has been exceeded (${spent:.2f} spent)."
        recommendation = "Pause non-essential spending in this category immediately. Review transactions for potential refunds."
    elif spent_pct >= 90:
        severity = "warning"
        message = f"{category} budget is at {spent_pct:.0f}% (${spent:.2f} / ${budget_limit:.2f})."
        recommendation = f"Reduce spending. Only ${budget_limit - spent:.2f} remaining. Consider deferring non-essential purchases."
    elif spent_pct >= 80:
        severity = "info"
        message = f"{category} budget at {spent_pct:.0f}% — approaching limit."
        recommendation = f"Monitor closely. ${budget_limit - spent:.2f} left. Prioritize essential spending."
    else:
        severity = "ok"
        message = f"{category} spending is on track ({spent_pct:.0f}% of ${budget_limit:.2f})."
        recommendation = "Continue current spending habits."

    logger.info("generate_budget_alert[%s]: severity=%s (%.1f%%)", category, severity, spent_pct)
    return {
        "category": category,
        "severity": severity,
        "message": message,
        "recommendation": recommendation,
        "spent_percentage": spent_pct,
        "budget_limit": round(budget_limit, 2),
    }


@tool("suggest_budget_adjustments")
def suggest_budget_adjustments(spending_history: list) -> dict:
    if not spending_history:
        return {"adjustments": [], "message": "No spending history available for analysis."}

    category_totals: Dict[str, float] = {}
    category_counts: Dict[str, int] = {}
    for entry in spending_history:
        cat = entry.get("category", "Other")
        category_totals[cat] = category_totals.get(cat, 0) + entry.get("amount", 0)
        category_counts[cat] = category_counts.get(cat, 1)

    total = sum(category_totals.values())
    adjustments = []
    for cat, amt in sorted(category_totals.items(), key=lambda x: -x[1]):
        pct = round(amt / total * 100, 1) if total > 0 else 0
        if pct > 35:
            suggested_limit = round(amt * 0.85, -1)
            adjustments.append({
                "category": cat,
                "suggested_limit": max(suggested_limit, 50),
                "current_avg": round(amt, 2),
                "reason": f"{cat} is {pct}% of total spending. Reducing by 15% frees up funds.",
            })
        elif pct < 5:
            adjustments.append({
                "category": cat,
                "suggested_limit": max(round(amt * 1.1, -0), 25),
                "current_avg": round(amt, 2),
                "reason": f"{cat} is only {pct}% — consider slight increase if needed.",
            })

    logger.info("suggest_budget_adjustments: %d suggestions", len(adjustments))
    return {
        "adjustments": adjustments,
        "total_spending": round(total, 2),
        "total_categories": len(category_totals),
    }


class BudgetMonitorAgent:
    """ReACT-based agent for monitoring budgets, checking thresholds, and generating alerts."""

    def __init__(self) -> None:
        self.memory = AgentMemory()
        self.thinking_state: str = ""
        self.current_cycle: int = 0
        self.task_complete: bool = False
        self.task_result: Any = None
        self.error_count: int = 0
        self.executed_actions: List[str] = []
        self.tool_registry = TOOL_REGISTRY

    def _think(self, message: str) -> None:
        self.thinking_state = message
        self.memory.add_thought(message, self.current_cycle)
        logger.info("[BUDGET THINK] %s", message)

    def _act(self, tool_name: str, **kwargs) -> Any:
        self.executed_actions.append(tool_name)
        self.memory.add_action(tool_name, kwargs, self.current_cycle)
        logger.info("[BUDGET ACT] Calling %s with %s", tool_name, kwargs)
        if tool_name in self.tool_registry:
            try:
                result = self.tool_registry[tool_name](**kwargs)
                self.memory.add_observation(tool_name, result, self.current_cycle)
                return result
            except Exception as e:
                logger.error("[BUDGET ERROR] Tool %s failed: %s", tool_name, e)
                self.error_count += 1
                return {"error": str(e)}
        logger.warning("[BUDGET] Unknown tool: %s", tool_name)
        return {"error": f"Unknown tool: {tool_name}"}

    def _observe(self, tool_name: str, result: Any) -> str:
        obs = f"Tool '{tool_name}' returned: {str(result)[:200]}"
        logger.info("[BUDGET OBSERVE] %s", obs)
        return obs

    def _reflect(self) -> str:
        if self.task_complete:
            reflection = "Budget monitoring task completed."
        else:
            last = self.executed_actions[-1] if self.executed_actions else "none"
            reflection = f"Completed '{last}'. Evaluating results for next step."
        self.memory.add_reflection(reflection, self.current_cycle)
        self.current_cycle += 1
        logger.info("[BUDGET REFLECT] %s", reflection)
        return reflection

    def monitor_user_budgets(self, user_id: str, budgets: list, transactions: list) -> list:
        self._think(f"Monitoring {len(budgets)} budgets for user '{user_id}'.")
        results = []

        for budget in budgets:
            cat = budget.get("category", "Unknown")
            limit = budget.get("monthly_limit", budget.get("limit", 0))
            spent = sum(
                t.get("amount", 0)
                for t in transactions
                if t.get("category", "") == cat
            )
            budget_id = budget.get("budget_id", budget.get("id", ""))

            status = self._act("check_budget_status",
                budget_id=budget_id, category=cat, spent=spent, limit=limit)
            self._observe("check_budget_status", status)

            velocity = self._act("analyze_spending_velocity",
                category=cat, days_into_month=15, spent=spent, limit=limit)
            self._observe("analyze_spending_velocity", velocity)

            spent_pct = status.get("spent_percentage", 0)
            if spent_pct >= 80:
                alert = self._act("generate_budget_alert",
                    category=cat, spent_pct=spent_pct, budget_limit=limit, spent=spent)
                self._observe("generate_budget_alert", alert)
            else:
                alert = {"severity": "ok", "message": f"{cat} is on track.", "recommendation": "No action needed."}

            results.append({
                "category": cat,
                "status": status,
                "velocity": velocity,
                "alert": alert,
            })

        self._reflect()
        return results

    def check_all_thresholds(self, user_id: str, budgets: list, transactions: list) -> dict:
        self._think(f"Checking thresholds for user '{user_id}'.")
        alerts = []
        critical_count = 0
        warning_count = 0

        for budget in budgets:
            cat = budget.get("category", "Unknown")
            limit = budget.get("monthly_limit", budget.get("limit", 0))
            spent = sum(
                t.get("amount", 0)
                for t in transactions
                if t.get("category", "") == cat
            )
            spent_pct = round(spent / limit * 100, 1) if limit > 0 else 0
            budget_id = budget.get("budget_id", budget.get("id", ""))

            status = self._act("check_budget_status",
                budget_id=budget_id, category=cat, spent=spent, limit=limit)
            threshold = status.get("status", "ok")
            alert = self._act("generate_budget_alert",
                category=cat, spent_pct=spent_pct, budget_limit=limit, spent=spent)
            alerts.append(alert)

            if threshold in ("exceeded", "critical"):
                critical_count += 1
            elif threshold == "warning":
                warning_count += 1

        self._reflect()
        return {
            "user_id": user_id,
            "total_budgets": len(budgets),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "ok_count": len(budgets) - critical_count - warning_count,
            "alerts": alerts,
            "cycle_log": {
                "actions": self.memory.action_history,
                "observations": self.memory.observations,
            },
        }

    def generate_daily_report(self, user_id: str, budgets: list, transactions: list) -> str:
        self._think(f"Generating daily budget report for user '{user_id}'.")
        lines = [f"=== Daily Budget Report for {user_id} ==="]

        for budget in budgets:
            cat = budget.get("category", "Unknown")
            limit = budget.get("monthly_limit", budget.get("limit", 0))
            spent = sum(
                t.get("amount", 0)
                for t in transactions
                if t.get("category", "") == cat
            )
            spent_pct = round(spent / limit * 100, 1) if limit > 0 else 0

            budget_id = budget.get("budget_id", budget.get("id", ""))
            status = self._act("check_budget_status",
                budget_id=budget_id, category=cat, spent=spent, limit=limit)
            velocity = self._act("analyze_spending_velocity",
                category=cat, days_into_month=15, spent=spent, limit=limit)

            remaining = status.get("remaining", 0)
            will_exceed = velocity.get("will_exceed", False)

            flag = "!!" if spent_pct >= 80 else "OK"
            exceed_flag = " OVER" if will_exceed else ""
            lines.append(f"  [{flag}] {cat}: ${spent:.0f}/${limit:.0f} ({spent_pct:.0f}%){exceed_flag} — ${remaining:.0f} left")

        self._reflect()
        lines.append(f"=== Report Complete ===")
        return "\n".join(lines)

    def suggest_reallocations(self, user_id: str, budgets: list, transactions: list) -> dict:
        self._think(f"Analyzing budget reallocations for user '{user_id}'.")
        self._act("suggest_budget_adjustments", spending_history=transactions)
        self._observe("suggest_budget_adjustments",
            self.memory.get_observation("suggest_budget_adjustments"))

        adjustments = self.memory.get_observation("suggest_budget_adjustments") or {}
        adjustment_list = adjustments.get("adjustments", [])

        self._reflect()
        return {
            "user_id": user_id,
            "reallocations": adjustment_list,
            "summary": adjustments.get("message", f"{len(adjustment_list)} reallocation(s) suggested."),
            "cycle_log": {
                "actions": self.memory.action_history,
                "observations": self.memory.observations,
            },
        }

    def get_state(self) -> dict:
        return {
            "thinking_state": self.thinking_state,
            "current_cycle": self.current_cycle,
            "task_complete": self.task_complete,
            "error_count": self.error_count,
            "executed_actions": self.executed_actions,
            "memory_summary": self.memory.to_summary(),
        }

    def reset(self) -> None:
        self.memory.clear()
        self.thinking_state = ""
        self.current_cycle = 0
        self.task_complete = False
        self.task_result = None
        self.error_count = 0
        self.executed_actions.clear()
