"""
GoalPlannerAgent — ReACT-based agent that analyzes spending patterns,
suggests SMART financial goals, and creates actionable savings plans.
"""
import logging
import uuid
from datetime import datetime, timedelta
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


@tool("analyze_spending_pattern")
def analyze_spending_pattern(transactions: list) -> dict:
    if not transactions:
        return {"spending_by_category": {}, "avg_monthly": 0, "trends": {}, "message": "No transactions to analyze"}

    by_category: Dict[str, float] = {}
    monthly: Dict[str, float] = {}
    for t in transactions:
        cat = t.get("category", "Other")
        by_category[cat] = by_category.get(cat, 0) + t.get("amount", 0)
        date_str = t.get("date", "")
        month = date_str[:7] if len(date_str) >= 7 else "unknown"
        monthly[month] = monthly.get(month, 0) + t.get("amount", 0)

    months = sorted(monthly.keys())
    trends: Dict[str, Any] = {}
    if len(months) >= 2:
        first, last = monthly[months[0]], monthly[months[-1]]
        trends["direction"] = "increasing" if last > first else "decreasing" if first > last else "stable"
        trends["change_pct"] = round((last - first) / max(first, 0.01) * 100, 1)
    else:
        trends["direction"] = "insufficient_data"

    total = sum(by_category.values())
    breakdown = {
        cat: {"amount": round(amt, 2), "percentage": round(amt / total * 100, 1) if total > 0 else 0}
        for cat, amt in sorted(by_category.items(), key=lambda x: -x[1])
    }
    avg_monthly = round(total / max(len(months), 1), 2)

    logger.info("analyze_spending_pattern: %d categories, avg_monthly=%.2f", len(breakdown), avg_monthly)
    return {
        "spending_by_category": breakdown,
        "avg_monthly": avg_monthly,
        "trends": trends,
        "total_txns": len(transactions),
    }


@tool("calculate_goal_timeline")
def calculate_goal_timeline(target_amount: float, current_savings: float, monthly_saveable: float) -> dict:
    if monthly_saveable <= 0:
        return {"months_needed": float("inf"), "weekly_target": 0, "action_items": ["Increase monthly savings capacity"]}

    remaining = max(target_amount - current_savings, 0)
    months_needed = round(remaining / monthly_saveable, 1)
    weekly_target = round(monthly_saveable / 4.33, 2)

    action_items = [
        f"Set aside ${monthly_saveable:.2f} per month (${weekly_target:.2f}/week)",
    ]
    if months_needed > 24:
        action_items.append("Consider extending timeline or increasing savings rate")
        action_items.append("Look for opportunities to reduce discretionary spending")
    elif months_needed > 12:
        action_items.append("Mid-range goal — review quarterly to stay on track")
        action_items.append("Automate monthly transfers to a dedicated savings account")
    else:
        action_items.append("Short-term goal — consider high-yield savings for maximum growth")
        action_items.append("Track weekly progress to maintain momentum")

    logger.info("calculate_goal_timeline: target=%.2f, need %.1f months", target_amount, months_needed)
    return {
        "months_needed": months_needed,
        "weekly_target": weekly_target,
        "monthly_target": monthly_saveable,
        "action_items": action_items,
        "remaining": remaining,
    }


@tool("suggest_goals")
def suggest_goals(spending_data: dict, user_preferences: str = "") -> list:
    avg_monthly = spending_data.get("avg_monthly", 0)
    by_category = spending_data.get("spending_by_category", {})
    suggestions = []

    if avg_monthly <= 0:
        return [{"name": "Track expenses first", "target": 0, "timeline": "1 month", "why": "Start tracking to understand your spending patterns"}]

    top_cat = max(by_category, key=lambda c: by_category[c]["amount"]) if by_category else None
    if top_cat:
        top_pct = by_category[top_cat]["percentage"]
        if top_pct > 30:
            suggestions.append({
                "name": f"Reduce {top_cat} Spending",
                "target": round(avg_monthly * 0.1 * 6, 0),
                "timeline": "6 months",
                "why": f"{top_cat} is {top_pct}% of your spending. Saving 10% monthly builds a buffer.",
            })

    emergency_target = round(avg_monthly * 3, -2)
    suggestions.append({
        "name": "Emergency Fund",
        "target": emergency_target,
        "timeline": f"{max(round(emergency_target / max(avg_monthly * 0.2, 1), 1), 6)} months",
        "why": f"3 months of expenses ({emergency_target}) provides financial security.",
    })

    vacation_target = round(avg_monthly * 0.5, -2)
    suggestions.append({
        "name": "Vacation Fund",
        "target": vacation_target,
        "timeline": f"{max(round(vacation_target / max(avg_monthly * 0.15, 1), 1), 3)} months",
        "why": f"Set aside {vacation_target} for your next trip without dipping into savings.",
    })

    logger.info("suggest_goals: generated %d suggestions", len(suggestions))
    return suggestions


@tool("generate_goal_action_plan")
def generate_goal_action_plan(goal: dict) -> dict:
    name = goal.get("goal_name", goal.get("name", "Unnamed Goal"))
    target = goal.get("target_amount", goal.get("target", 0))
    current = goal.get("current_amount", goal.get("current", 0))
    monthly = goal.get("monthly_contribution", goal.get("monthly_saveable", 0))
    remaining = max(target - current, 0)
    months = max(round(remaining / max(monthly, 1)), 1)

    weekly = round(remaining / (months * 4.33), 2)
    milestones = [{"week": w, "target": round(weekly * w, 2)} for w in range(1, min(months * 4, 13), 1)]
    monthly_targets = [{"month": m, "target": round(current + monthly * m, 2)} for m in range(1, min(months + 1, 13))]

    obstacles = [
        "Unexpected expenses requiring budget reallocation",
        "Loss or reduction of income",
        "Temptation to dip into savings for non-essential purchases",
    ]
    if months > 12:
        obstacles.append("Long timeline may lead to loss of motivation")
        obstacles.append("Inflation may reduce purchasing power of savings")

    strategies = [
        f"Automate ${monthly:.2f} monthly transfer to a dedicated account",
        "Review progress monthly and adjust contributions as income changes",
        "Celebrate milestones (25%, 50%, 75%) to stay motivated",
    ]
    if remaining > 10000:
        strategies.append("Consider splitting into multiple sub-goals for better tracking")
        strategies.append("Explore investment options for long-term growth")

    logger.info("generate_goal_action_plan: '%s' — %d months plan", name, months)
    return {
        "goal_name": name,
        "total_months": months,
        "weekly_milestones": milestones,
        "monthly_targets": monthly_targets,
        "weekly_savings_target": weekly,
        "monthly_savings_target": monthly,
        "obstacles": obstacles,
        "strategies": strategies,
    }


class GoalPlannerAgent:
    """ReACT-based agent for analyzing spending, suggesting goals, and creating action plans."""

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
        logger.info("[PLANNER THINK] %s", message)

    def _act(self, tool_name: str, **kwargs) -> Any:
        self.executed_actions.append(tool_name)
        self.memory.add_action(tool_name, kwargs, self.current_cycle)
        logger.info("[PLANNER ACT] Calling %s with %s", tool_name, kwargs)
        if tool_name in self.tool_registry:
            try:
                result = self.tool_registry[tool_name](**kwargs)
                self.memory.add_observation(tool_name, result, self.current_cycle)
                return result
            except Exception as e:
                logger.error("[PLANNER ERROR] Tool %s failed: %s", tool_name, e)
                self.error_count += 1
                return {"error": str(e)}
        logger.warning("[PLANNER] Unknown tool: %s", tool_name)
        return {"error": f"Unknown tool: {tool_name}"}

    def _observe(self, tool_name: str, result: Any) -> str:
        obs = f"Tool '{tool_name}' returned: {str(result)[:200]}"
        logger.info("[PLANNER OBSERVE] %s", obs)
        return obs

    def _reflect(self) -> str:
        if self.task_complete:
            reflection = "Goal planning task completed."
        else:
            last = self.executed_actions[-1] if self.executed_actions else "none"
            reflection = f"Completed '{last}'. Analyzing results for next step."
        self.memory.add_reflection(reflection, self.current_cycle)
        self.current_cycle += 1
        logger.info("[PLANNER REFLECT] %s", reflection)
        return reflection

    def process_goal_request(self, user_id: str, goal_description: str, transactions: list) -> dict:
        self._think(f"User '{user_id}' wants to: {goal_description}. Analyzing financial situation.")
        spending_data = self._act("analyze_spending_pattern", transactions=transactions)
        if "error" in spending_data:
            return {"error": spending_data["error"]}
        self._observe("analyze_spending_pattern", spending_data)

        suggestions = self._act("suggest_goals", spending_data=spending_data, user_preferences=goal_description)
        self._observe("suggest_goals", suggestions)

        action_plans = []
        for sg in (suggestions if isinstance(suggestions, list) else suggestions.get("suggestions", [])):
            timeline = self._act("calculate_goal_timeline",
                target_amount=sg.get("target", 5000),
                current_savings=0,
                monthly_saveable=max(spending_data.get("avg_monthly", 0) * 0.15, 50),
            )
            plan = self._act("generate_goal_action_plan", goal={**sg, **timeline})
            action_plans.append(plan)

        self._reflect()
        return {
            "user_id": user_id,
            "spending_analysis": spending_data,
            "suggested_goals": suggestions,
            "action_plans": action_plans,
            "cycle_log": {
                "thoughts": self.memory.thought_process,
                "actions": self.memory.action_history,
                "observations": self.memory.observations,
                "reflections": self.memory.reflections,
            },
        }

    def analyze_goal_feasibility(self, goal: dict) -> dict:
        self._think(f"Analyzing feasibility of goal: {goal.get('goal_name', 'Unnamed')}")
        target = goal.get("target_amount", goal.get("target", 0))
        current = goal.get("current_amount", goal.get("current", 0))
        monthly = goal.get("monthly_contribution", goal.get("monthly_saveable", 0))
        deadline_str = goal.get("deadline", "")
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(str(deadline_str)[:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                pass
        remaining = max(target - current, 0)
        months_available = 12
        if deadline:
            months_available = max((deadline - datetime.utcnow()).days / 30, 0.5)
        needed_monthly = round(remaining / months_available, 2) if months_available > 0 else float("inf")
        feasible = monthly >= needed_monthly if monthly > 0 else False

        self._act("calculate_goal_timeline", target_amount=target, current_savings=current, monthly_saveable=monthly)
        self._reflect()
        return {
            "feasible": feasible or remaining <= 0,
            "remaining": remaining,
            "months_available": round(months_available, 1),
            "needed_monthly": needed_monthly,
            "current_monthly": monthly,
            "gap": round(max(needed_monthly - monthly, 0), 2),
        }

    def recommend_adjustments(self, goal: dict) -> str:
        feasibility = self.analyze_goal_feasibility(goal)
        if feasibility["feasible"]:
            return "Your goal is on track! Keep up the consistent savings."
        gap = feasibility["gap"]
        target = goal.get("target_amount", goal.get("target", 0))
        if gap > 0:
            pct_increase = round(gap / max(feasibility["current_monthly"], 0.01) * 100, 0)
            return (
                f"Goal needs adjustment. Try increasing monthly savings by ${gap:.0f} "
                f"({pct_increase:.0f}% increase) to meet the deadline. "
                f"Consider reducing non-essential spending or extending the timeline."
            )
        return "Unable to assess. Please provide goal details (target, savings, deadline)."

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
