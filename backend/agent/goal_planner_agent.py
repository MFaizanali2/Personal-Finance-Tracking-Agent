import logging
from datetime import datetime, timedelta

from backend.agent.agent import BaseAgent
from database import create_goal, add_to_goal

logger = logging.getLogger(__name__)


class GoalPlan:
    """Wrapper for a goal with computed properties."""

    def __init__(self, data: dict):
        self._data = data

    @property
    def name(self) -> str:
        return self._data.get("goal_name", "Unnamed")

    @property
    def target(self) -> float:
        return self._data.get("target_amount", 0)

    @property
    def timeline_months(self) -> int:
        return self._data.get("timeline_months", 12)

    @property
    def monthly_needed(self) -> float:
        if self.timeline_months <= 0:
            return self.target
        return round(self.target / self.timeline_months, 2)

    @property
    def priority(self) -> str:
        return self._data.get("priority", "medium")

    @property
    def goal_type(self) -> str:
        return self._data.get("goal_type", "short_term")

    def to_dict(self) -> dict:
        return {**self._data, "monthly_needed": self.monthly_needed}


class GoalPlannerAgent(BaseAgent):
    """ReACT-based agent for analyzing spending, suggesting goals, and creating action plans."""

    def __init__(self, gemini_api_key: str = ""):
        super().__init__(name="GoalPlanner", gemini_api_key=gemini_api_key)
        self._register_tools()

    def _register_tools(self):
        """Register all tools the agent can use."""
        self.register_tool(
            name="analyze_spending",
            func=self.analyze_spending_pattern,
            description="Analyzes user's transaction history to identify spending patterns, categories, and trends",
        )
        self.register_tool(
            name="calculate_savings",
            func=self.calculate_monthly_savings,
            description="Calculates how much user can save monthly based on spending analysis",
        )
        self.register_tool(
            name="suggest_goals",
            func=self.suggest_smart_goals,
            description="Suggests SMART (Specific, Measurable, Achievable, Relevant, Time-bound) financial goals",
        )
        self.register_tool(
            name="create_action_plan",
            func=self.create_goal_action_plan,
            description="Creates detailed action plan and milestones for achieving a goal",
        )

    def analyze_spending_pattern(self, user_id: str, transactions: list) -> dict:
        """Analyze spending patterns from user's transactions."""
        if not transactions:
            print("[ANALYZE] No transactions found")
            return {"error": "No transactions found"}

        total_spent = sum(t.get("amount", 0) for t in transactions)
        category_spending = {}
        for t in transactions:
            cat = t.get("category", "Other")
            category_spending[cat] = category_spending.get(cat, 0) + t.get("amount", 0)

        high_expense = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:3]
        avg_monthly = round(total_spent / max(1, len(transactions) // 30), 2) if len(transactions) > 30 else round(total_spent, 2)

        analysis = {
            "total_spent": round(total_spent, 2),
            "avg_monthly": avg_monthly,
            "by_category": category_spending,
            "high_expense_categories": [{"category": cat, "amount": amt} for cat, amt in high_expense],
            "transaction_count": len(transactions),
            "analysis_date": datetime.now().isoformat(),
        }

        print(f"[ANALYZE] Total spent: ${analysis['total_spent']} | Categories: {len(category_spending)}")
        logger.info("Spending analyzed: %.2f across %d txns", analysis["total_spent"], len(transactions))
        return analysis

    def calculate_monthly_savings(self, monthly_income: float, monthly_expenses: float, savings_rate: float = 0.2) -> dict:
        """Calculate how much user can save monthly."""
        available = monthly_income - monthly_expenses
        recommended_savings = available * savings_rate
        result = {
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "available_to_save": round(available, 2),
            "recommended_savings": round(recommended_savings, 2),
            "savings_rate_percentage": savings_rate * 100,
            "monthly_discretionary": round(available - recommended_savings, 2),
        }
        print(f"[SAVINGS] Available: ${available:.2f} | Recommended: ${recommended_savings:.2f}/month")
        return result

    def suggest_smart_goals(self, spending_analysis: dict, monthly_savings: float) -> list:
        """Suggest SMART financial goals based on spending analysis."""
        goals = []
        high_expenses = spending_analysis.get("high_expense_categories", [])

        if high_expenses:
            goals.append({
                "goal_name": "Emergency Fund",
                "goal_type": "long_term",
                "target_amount": sum(cat["amount"] for cat in high_expenses[:2]) * 3,
                "timeline_months": 12,
                "priority": "high",
                "why": f"Based on your spending of ${spending_analysis['avg_monthly']:.0f}/month, emergency fund should cover 3 months",
            })
        if monthly_savings > 500:
            goals.append({
                "goal_name": "Vacation Fund",
                "goal_type": "short_term",
                "target_amount": 2000,
                "timeline_months": 6,
                "priority": "medium",
                "why": "You have enough savings capacity for a short-term vacation goal",
            })
        if monthly_savings > 1000:
            goals.append({
                "goal_name": "Investment Portfolio",
                "goal_type": "long_term",
                "target_amount": 10000,
                "timeline_months": 24,
                "priority": "medium",
                "why": "Building long-term wealth through regular investments",
            })

        print(f"[GOALS] Suggested {len(goals)} goal(s)")
        logger.info("Suggested %d goals", len(goals))
        return goals

    def create_goal_action_plan(self, goal: dict) -> dict:
        """Create detailed action plan with milestones for a goal."""
        plan = GoalPlan(goal)
        target = plan.target
        timeline = plan.timeline_months
        monthly_needed = plan.monthly_needed
        step = max(1, timeline // 4)

        action_plan = {
            "goal_name": plan.name,
            "total_target": target,
            "timeline_months": timeline,
            "monthly_savings_needed": monthly_needed,
            "milestones": [
                {
                    "month": i,
                    "target_amount": round(monthly_needed * i, 2),
                    "achievement": f"{round((monthly_needed * i / target) * 100, 1) if target > 0 else 0}% complete",
                }
                for i in range(1, timeline + 1, step)
            ],
            "obstacles": ["Unexpected expenses", "Income fluctuation", "Lifestyle inflation"],
            "strategies": [
                "Set up automatic monthly transfers",
                "Track progress weekly",
                "Review and adjust budgets monthly",
                "Celebrate milestones",
            ],
            "created_at": datetime.now().isoformat(),
        }

        print(f"[PLAN] {plan.name}: ${monthly_needed:.0f}/month for {timeline} months")
        logger.info("Action plan created: %.2f/month needed", monthly_needed)
        return action_plan

    def process(self, user_id: str, transactions: list, monthly_income: float) -> dict:
        """Run the full goal planning ReACT loop: analyze → calculate → suggest → plan."""
        print(f"\n{'='*50}")
        print(f"[PROCESS] GoalPlanner analyzing for user '{user_id}'")
        print(f"{'='*50}")

        self.memory.clear()
        self.thinking_history.clear()

        # THINK & ACT: Analyze spending
        print("\n--- STEP 1: Analyze Spending Patterns ---")
        spending_analysis = self.analyze_spending_pattern(user_id, transactions)

        # THINK & ACT: Calculate savings capacity
        print("\n--- STEP 2: Calculate Savings Capacity ---")
        monthly_expenses = spending_analysis.get("avg_monthly", 0)
        savings_calc = self.calculate_monthly_savings(monthly_income, monthly_expenses)
        monthly_savings = savings_calc.get("recommended_savings", 0)

        # THINK & ACT: Suggest goals
        print("\n--- STEP 3: Suggest SMART Goals ---")
        suggested_goals = self.suggest_smart_goals(spending_analysis, monthly_savings)

        # THINK & ACT: Create action plans
        print("\n--- STEP 4: Create Action Plans ---")
        action_plans = [self.create_goal_action_plan(g) for g in suggested_goals]

        # OBSERVE & store
        result = {
            "user_id": user_id,
            "spending_analysis": spending_analysis,
            "savings_capacity": savings_calc,
            "suggested_goals": suggested_goals,
            "action_plans": action_plans,
            "timestamp": datetime.now().isoformat(),
        }

        self.memory.append(result)
        print(f"\n{'='*50}")
        print(f"[DONE] {len(suggested_goals)} goal(s) generated for user '{user_id}'")
        print(f"{'='*50}")

        return result


def process_goal_request(user_id: str, transactions: list, monthly_income: float) -> dict:
    """Convenience function: create agent, run process, return result."""
    agent = GoalPlannerAgent()
    return agent.process(user_id, transactions, monthly_income)
