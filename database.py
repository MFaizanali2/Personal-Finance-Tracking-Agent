import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from schemas import GoalSchema, BudgetSchema

logger = logging.getLogger(__name__)

VALID_CATEGORIES: List[str] = [
    "Food", "Rent", "Transport", "Entertainment",
    "Medical", "Shopping", "Utilities", "Other",
]


class MockDatabase:
    def __init__(self) -> None:
        self._storage: Dict[str, Dict[str, Any]] = {}
        self.goals_db: Dict[str, List[Dict[str, Any]]] = {}
        self.budgets_db: Dict[str, List[Dict[str, Any]]] = {}

    def _make_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "id": str(uuid.uuid4()),
            "amount": float(data.get("amount", 0)),
            "category": data.get("category", "Other"),
            "description": data.get("description", ""),
            "date": data.get("date", now.strftime("%Y-%m-%d")),
            "created_at": now.isoformat(),
            "agent_confidence": round(float(data.get("agent_confidence", 1.0)), 2),
            "status": data.get("status", "pending"),
        }

    def add_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        record = self._make_record(transaction)
        self._storage[record["id"]] = record
        logger.info(
            "Transaction added: %s (%.2f, %s)",
            record["id"], record["amount"], record["category"],
        )
        return dict(record)

    def add_transactions_batch(
        self, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        records = [self.add_transaction(t) for t in transactions]
        logger.info("Batch added %d transactions", len(records))
        return records

    def get_all_transactions(
        self, sort_by: Optional[str] = None, reverse: bool = False
    ) -> List[Dict[str, Any]]:
        results = [dict(r) for r in self._storage.values()]
        if sort_by and sort_by in ("amount", "date", "created_at", "category"):
            results.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
        return results

    def get_transaction_by_id(self, txn_id: str) -> Optional[Dict[str, Any]]:
        record = self._storage.get(txn_id)
        return dict(record) if record else None

    def get_transactions_by_category(self, category: str) -> List[Dict[str, Any]]:
        return [
            dict(r) for r in self._storage.values()
            if r["category"].lower() == category.lower()
        ]

    def get_transactions_by_date_range(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        return [
            dict(r) for r in self._storage.values()
            if start_date <= r["date"] <= end_date
        ]

    def get_transactions_by_status(self, status: str) -> List[Dict[str, Any]]:
        return [
            dict(r) for r in self._storage.values()
            if r["status"].lower() == status.lower()
        ]

    def search_transactions(self, keyword: str) -> List[Dict[str, Any]]:
        kw = keyword.lower()
        return [
            dict(r) for r in self._storage.values()
            if kw in r["description"].lower()
            or kw in r["category"].lower()
        ]

    def get_category_summary(self) -> List[Dict[str, Any]]:
        totals: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        for r in self._storage.values():
            cat = r["category"]
            totals[cat] = totals.get(cat, 0) + r["amount"]
            counts[cat] = counts.get(cat, 0) + 1
        return [
            {"category": c, "count": counts[c], "total": round(totals[c], 2)}
            for c in sorted(totals)
        ]

    def get_total_spent(self) -> float:
        return round(sum(r["amount"] for r in self._storage.values()), 2)

    def get_average_transaction(self) -> float:
        count = self.count()
        if count == 0:
            return 0.0
        return round(self.get_total_spent() / count, 2)

    def update_transaction(
        self, txn_id: str, updated_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        record = self._storage.get(txn_id)
        if record is None:
            return None
        for key in ("amount", "category", "description", "date", "status", "agent_confidence"):
            if key in updated_data:
                record[key] = updated_data[key]
        self._storage[txn_id] = record
        logger.info("Transaction updated: %s", txn_id)
        return dict(record)

    def update_transaction_status(
        self, txn_id: str, status: str
    ) -> Optional[Dict[str, Any]]:
        return self.update_transaction(txn_id, {"status": status})

    def delete_transaction(self, txn_id: str) -> bool:
        if txn_id in self._storage:
            del self._storage[txn_id]
            logger.info("Transaction deleted: %s", txn_id)
            return True
        return False

    def delete_transactions_by_category(self, category: str) -> int:
        ids = [
            rid for rid, r in self._storage.items()
            if r["category"].lower() == category.lower()
        ]
        for rid in ids:
            del self._storage[rid]
        if ids:
            logger.info("Deleted %d transactions in category '%s'", len(ids), category)
        return len(ids)

    def count(self) -> int:
        return len(self._storage)

    def clear(self) -> None:
        self._storage.clear()
        self.goals_db.clear()
        self.budgets_db.clear()
        logger.info("Database cleared")

    # ─── GOALS CRUD ─────────────────────────────────────────────────────────

    def _make_goal_record(self, user_id: str, goal: GoalSchema) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        goal_id = str(uuid.uuid4())
        record = {
            "goal_id": goal_id,
            "user_id": user_id,
            "goal_name": goal.goal_name,
            "goal_type": goal.goal_type,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "deadline": goal.deadline.isoformat() if hasattr(goal.deadline, 'isoformat') else str(goal.deadline),
            "priority": goal.priority,
            "status": goal.status,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "description": goal.description,
        }
        print(f"[DB] Goal record created: {goal_id} — {goal.goal_name}")
        return record

    def create_goal(self, user_id: str, goal: GoalSchema) -> Dict[str, Any]:
        record = self._make_goal_record(user_id, goal)
        if user_id not in self.goals_db:
            self.goals_db[user_id] = []
        self.goals_db[user_id].append(record)
        logger.info("Goal created for user %s: %s (%s)", user_id, record["goal_id"], goal.goal_name)
        return dict(record)

    def get_user_goals(self, user_id: str) -> List[Dict[str, Any]]:
        goals = self.goals_db.get(user_id, [])
        print(f"[DB] Retrieved {len(goals)} goals for user '{user_id}'")
        return [dict(g) for g in goals]

    def get_goal_by_id(self, goal_id: str) -> Optional[Dict[str, Any]]:
        for goals in self.goals_db.values():
            for g in goals:
                if g["goal_id"] == goal_id:
                    print(f"[DB] Found goal: {g['goal_name']} ({goal_id})")
                    return dict(g)
        print(f"[DB] Goal not found: {goal_id}")
        return None

    def update_goal(self, goal_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for user_goals in self.goals_db.values():
            for g in user_goals:
                if g["goal_id"] == goal_id:
                    allowed = {"goal_name", "goal_type", "target_amount", "current_amount",
                               "deadline", "priority", "status", "description"}
                    for key in updates:
                        if key in allowed:
                            g[key] = updates[key]
                    g["updated_at"] = datetime.now(timezone.utc).isoformat()
                    logger.info("Goal updated: %s", goal_id)
                    print(f"[DB] Goal {goal_id} updated with {len(updates)} field(s)")
                    return dict(g)
        print(f"[DB] Cannot update: goal {goal_id} not found")
        return None

    def delete_goal(self, goal_id: str) -> bool:
        for user_id, goals in self.goals_db.items():
            for i, g in enumerate(goals):
                if g["goal_id"] == goal_id:
                    self.goals_db[user_id].pop(i)
                    logger.info("Goal deleted: %s", goal_id)
                    print(f"[DB] Goal {goal_id} deleted")
                    return True
        print(f"[DB] Cannot delete: goal {goal_id} not found")
        return False

    def add_to_goal(self, goal_id: str, amount: float) -> Optional[Dict[str, Any]]:
        for user_goals in self.goals_db.values():
            for g in user_goals:
                if g["goal_id"] == goal_id:
                    g["current_amount"] = round(g["current_amount"] + amount, 2)
                    g["updated_at"] = datetime.now(timezone.utc).isoformat()
                    logger.info("Added %.2f to goal %s (now %.2f)", amount, goal_id, g["current_amount"])
                    print(f"[DB] Added ${amount:.2f} to goal '{g['goal_name']}'")
                    return dict(g)
        print(f"[DB] Cannot add to goal {goal_id}: not found")
        return None

    def check_goal_completion(self, goal_id: str) -> bool:
        for user_goals in self.goals_db.values():
            for g in user_goals:
                if g["goal_id"] == goal_id:
                    completed = g["current_amount"] >= g["target_amount"]
                    if completed:
                        g["status"] = "completed"
                        g["updated_at"] = datetime.now(timezone.utc).isoformat()
                        logger.info("Goal completed: %s", goal_id)
                        print(f"[DB] Goal '{g['goal_name']}' is now COMPLETE!")
                    return completed
        print(f"[DB] Cannot check completion: goal {goal_id} not found")
        return False

    # ─── BUDGETS CRUD ───────────────────────────────────────────────────────

    def _make_budget_record(self, user_id: str, budget: BudgetSchema) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        budget_id = str(uuid.uuid4())
        record = {
            "budget_id": budget_id,
            "user_id": user_id,
            "category": budget.category,
            "monthly_limit": budget.monthly_limit,
            "spent_so_far": budget.spent_so_far,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "month": budget.month,
        }
        print(f"[DB] Budget record created: {budget_id} — {budget.category} (${budget.monthly_limit:.2f})")
        return record

    def create_budget(self, user_id: str, budget: BudgetSchema) -> Dict[str, Any]:
        record = self._make_budget_record(user_id, budget)
        if user_id not in self.budgets_db:
            self.budgets_db[user_id] = []
        self.budgets_db[user_id].append(record)
        logger.info("Budget created for user %s: %s (%s)", user_id, record["budget_id"], budget.category)
        return dict(record)

    def get_user_budgets(self, user_id: str, month: Optional[str] = None) -> List[Dict[str, Any]]:
        budgets = self.budgets_db.get(user_id, [])
        if month:
            budgets = [b for b in budgets if b["month"] == month]
        print(f"[DB] Retrieved {len(budgets)} budgets for user '{user_id}' (month={month})")
        return [dict(b) for b in budgets]

    def get_budget_by_id(self, budget_id: str) -> Optional[Dict[str, Any]]:
        for budgets in self.budgets_db.values():
            for b in budgets:
                if b["budget_id"] == budget_id:
                    print(f"[DB] Found budget: {b['category']} ({budget_id})")
                    return dict(b)
        print(f"[DB] Budget not found: {budget_id}")
        return None

    def update_budget(self, budget_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for user_budgets in self.budgets_db.values():
            for b in user_budgets:
                if b["budget_id"] == budget_id:
                    allowed = {"category", "monthly_limit", "spent_so_far", "month"}
                    for key in updates:
                        if key in allowed:
                            b[key] = updates[key]
                    b["updated_at"] = datetime.now(timezone.utc).isoformat()
                    logger.info("Budget updated: %s", budget_id)
                    print(f"[DB] Budget {budget_id} updated with {len(updates)} field(s)")
                    return dict(b)
        print(f"[DB] Cannot update: budget {budget_id} not found")
        return None

    def delete_budget(self, budget_id: str) -> bool:
        for user_id, budgets in self.budgets_db.items():
            for i, b in enumerate(budgets):
                if b["budget_id"] == budget_id:
                    self.budgets_db[user_id].pop(i)
                    logger.info("Budget deleted: %s", budget_id)
                    print(f"[DB] Budget {budget_id} deleted")
                    return True
        print(f"[DB] Cannot delete: budget {budget_id} not found")
        return False

    def check_budget_alerts(self, user_id: str, category: str) -> Dict[str, Any]:
        budgets = self.budgets_db.get(user_id, [])
        for b in budgets:
            if b["category"].lower() == category.lower():
                limit = b["monthly_limit"]
                spent = b["spent_so_far"]
                pct = round(spent / limit * 100, 1) if limit > 0 else 0
                triggered = []
                if pct >= 100:
                    triggered.append({"level": 100, "message": f"{category} budget EXCEEDED! ${spent:.2f} / ${limit:.2f}"})
                elif pct >= 80:
                    triggered.append({"level": 80, "message": f"{category} budget at {pct}% (${spent:.2f} / ${limit:.2f})"})
                result = {
                    "budget_id": b["budget_id"],
                    "category": category,
                    "monthly_limit": limit,
                    "spent_so_far": spent,
                    "percentage": pct,
                    "alerts_triggered": triggered,
                    "alert_count": len(triggered),
                }
                print(f"[DB] Budget alerts for {category}: {len(triggered)} alert(s)")
                return result
        print(f"[DB] No budget found for category '{category}' (user {user_id})")
        return {"category": category, "alerts_triggered": [], "alert_count": 0, "message": "No budget set"}

    def __repr__(self) -> str:
        return f"MockDatabase(transactions={self.count()}, goals={sum(len(v) for v in self.goals_db.values())}, budgets={sum(len(v) for v in self.budgets_db.values())})"


# ============================================================================
# GOAL MANAGEMENT FUNCTIONS
# ============================================================================

goals_db = {}          # {user_id: [goal_objects]}
budgets_db = {}        # {user_id: {month: [budget_objects]}}


# ----- GOAL CRUD OPERATIONS -----

def create_goal(user_id: str, goal_data: dict) -> dict:
    """Create a new goal"""
    from uuid import uuid4

    if user_id not in goals_db:
        goals_db[user_id] = []

    deadline = goal_data.get("deadline")
    if hasattr(deadline, "isoformat"):
        deadline = deadline.isoformat()

    goal = {
        "goal_id": str(uuid4()),
        "user_id": user_id,
        "goal_name": goal_data.get("goal_name"),
        "goal_type": goal_data.get("goal_type"),
        "target_amount": float(goal_data.get("target_amount", 0)),
        "current_amount": 0.0,
        "deadline": deadline,
        "priority": goal_data.get("priority"),
        "status": "active",
        "description": goal_data.get("description", ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    goals_db[user_id].append(goal)
    print(f"Goal created: {goal['goal_id']}")
    return goal


def get_user_goals(user_id: str) -> list:
    """Get all goals for user"""
    return goals_db.get(user_id, [])


def get_goal_by_id(goal_id: str) -> dict or None:
    """Get single goal by ID"""
    for user_id in goals_db:
        for goal in goals_db[user_id]:
            if goal["goal_id"] == goal_id:
                return goal
    return None


def update_goal(goal_id: str, updates: dict) -> dict or None:
    """Update goal"""
    goal = get_goal_by_id(goal_id)
    if not goal:
        return None

    for key, value in updates.items():
        if key not in ["goal_id", "user_id", "created_at"]:
            goal[key] = value

    goal["updated_at"] = datetime.now().isoformat()
    return goal


def delete_goal(goal_id: str) -> bool:
    """Delete goal"""
    for user_id in goals_db:
        for i, goal in enumerate(goals_db[user_id]):
            if goal["goal_id"] == goal_id:
                goals_db[user_id].pop(i)
                return True
    return False


def add_to_goal(goal_id: str, amount: float) -> dict or None:
    """Add progress to goal"""
    goal = get_goal_by_id(goal_id)
    if not goal:
        return None

    goal["current_amount"] += float(amount)
    goal["updated_at"] = datetime.now().isoformat()

    if goal["current_amount"] >= goal["target_amount"]:
        goal["status"] = "completed"

    return goal


def get_goal_progress_percentage(goal_id: str) -> float:
    """Get goal progress %"""
    goal = get_goal_by_id(goal_id)
    if not goal or goal["target_amount"] == 0:
        return 0.0
    return round((goal["current_amount"] / goal["target_amount"]) * 100, 2)


# ============================================================================
# BUDGET MANAGEMENT FUNCTIONS
# ============================================================================

def create_budget(user_id: str, budget_data: dict) -> dict:
    """Create new budget"""
    from uuid import uuid4

    if user_id not in budgets_db:
        budgets_db[user_id] = {}

    month = budget_data.get("month")
    if month not in budgets_db[user_id]:
        budgets_db[user_id][month] = []

    budget = {
        "budget_id": str(uuid4()),
        "user_id": user_id,
        "category": budget_data.get("category"),
        "monthly_limit": float(budget_data.get("monthly_limit", 0)),
        "spent_so_far": 0.0,
        "month": month,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    budgets_db[user_id][month].append(budget)
    print(f"Budget created: {budget['budget_id']}")
    return budget


def get_user_transactions(user_id: str) -> list:
    """Get transactions for a user (delegates to MockDatabase)"""
    return MockDatabase().get_all_transactions()


def get_user_budgets(user_id: str, month: str) -> list:
    """Get budgets for user in month"""
    if user_id not in budgets_db:
        return []
    return budgets_db[user_id].get(month, [])


def get_budget_by_id(budget_id: str) -> dict or None:
    """Get single budget by ID"""
    for user_id in budgets_db:
        for month in budgets_db[user_id]:
            for budget in budgets_db[user_id][month]:
                if budget["budget_id"] == budget_id:
                    return budget
    return None


def update_budget(budget_id: str, updates: dict) -> dict or None:
    """Update budget"""
    budget = get_budget_by_id(budget_id)
    if not budget:
        return None

    for key, value in updates.items():
        if key not in ["budget_id", "user_id", "month", "created_at"]:
            budget[key] = value

    budget["updated_at"] = datetime.now().isoformat()
    return budget


def delete_budget(budget_id: str) -> bool:
    """Delete budget"""
    for user_id in budgets_db:
        for month in budgets_db[user_id]:
            for i, budget in enumerate(budgets_db[user_id][month]):
                if budget["budget_id"] == budget_id:
                    budgets_db[user_id][month].pop(i)
                    return True
    return False


def add_to_budget_spent(budget_id: str, amount: float) -> dict or None:
    """Add to budget spent amount"""
    budget = get_budget_by_id(budget_id)
    if not budget:
        return None

    budget["spent_so_far"] += float(amount)
    budget["updated_at"] = datetime.now().isoformat()
    return budget


def get_budget_spent_percentage(budget_id: str) -> float:
    """Get budget spent %"""
    budget = get_budget_by_id(budget_id)
    if not budget or budget["monthly_limit"] == 0:
        return 0.0
    return round((budget["spent_so_far"] / budget["monthly_limit"]) * 100, 2)


def get_budget_remaining(budget_id: str) -> float:
    """Get remaining budget"""
    budget = get_budget_by_id(budget_id)
    if not budget:
        return 0.0
    return round(budget["monthly_limit"] - budget["spent_so_far"], 2)


def check_budget_alerts(user_id: str, month: str) -> dict:
    """Check budget alerts for user"""
    budgets = get_user_budgets(user_id, month)

    alerts = {
        "warnings": [],
        "critical": [],
        "total_spent": 0.0,
        "total_limit": 0.0
    }

    for budget in budgets:
        spent_pct = get_budget_spent_percentage(budget["budget_id"])
        alerts["total_spent"] += budget["spent_so_far"]
        alerts["total_limit"] += budget["monthly_limit"]

        alert_item = {
            "budget_id": budget["budget_id"],
            "category": budget["category"],
            "spent": budget["spent_so_far"],
            "limit": budget["monthly_limit"],
            "percentage": spent_pct
        }

        if spent_pct >= 100:
            alert_item["status"] = "exceeded"
            alerts["critical"].append(alert_item)
        elif spent_pct >= 80:
            alert_item["status"] = "warning"
            alerts["warnings"].append(alert_item)

    return alerts


def get_budget_status(budget_id: str) -> str:
    """Get budget status"""
    pct = get_budget_spent_percentage(budget_id)
    if pct >= 100:
        return "exceeded"
    elif pct >= 80:
        return "warning"
    return "ok"
