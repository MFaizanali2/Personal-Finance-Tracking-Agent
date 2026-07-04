import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncGenerator, List
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent import ReACTAgent
from agent.goal_planner_agent import GoalPlannerAgent
from agent.budget_monitor_agent import BudgetMonitorAgent
from database import MockDatabase
from database import (
    create_goal, get_user_goals, get_goal_by_id, update_goal, delete_goal,
    add_to_goal, get_goal_progress_percentage,
    create_budget, get_user_budgets as get_user_budgets_fn, update_budget, delete_budget,
    add_to_budget_spent, get_budget_spent_percentage, check_budget_alerts,
    get_user_transactions,
)
from schemas import (
    AgentStateResponse,
    CategorySummary,
    ErrorResponse,
    HealthResponse,
    MessageResponse,
    TransactionInput,
    TransactionResponse,
    TransactionUpdate,
    GoalSchema, GoalCreate, BudgetSchema, BudgetCreate,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

agent = ReACTAgent()
db = MockDatabase()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("=" * 60)
    logger.info("Finance Tracker Agent starting up")
    logger.info("=" * 60)
    yield
    logger.info("Finance Tracker Agent shutting down")


app = FastAPI(
    title="Personal Finance Tracker Agent",
    description="ReACT-powered agent for personal finance management. "
    "Provides transaction validation, expense categorization, "
    "and financial summary generation through an intelligent agent loop.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _log_request(method: str, path: str) -> None:
    logger.info("[API] %s %s", method, path)


def _txn_to_response(txn: dict) -> TransactionResponse:
    return TransactionResponse(
        id=txn["id"],
        amount=txn["amount"],
        category=txn["category"],
        description=txn["description"],
        date=txn["date"],
        created_at=txn["created_at"],
        agent_confidence=txn["agent_confidence"],
        status=txn["status"],
    )


# ─── System ─────────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    return {"status": "alive", "version": "0.1.0"}


# ─── Transactions ────────────────────────────────────────────────────────────


@app.post(
    "/api/transactions/add",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
    tags=["Transactions"],
    summary="Add and process a new transaction",
)
def add_transaction(payload: TransactionInput):
    _log_request("POST", "/api/transactions/add")
    logger.info("[AGENT] Processing transaction: %.2f %s", payload.amount, payload.category)

    agent.reset()
    processed = agent.process_transaction(
        amount=payload.amount,
        category=payload.category,
        description=payload.description,
        date=payload.date,
    )

    if processed.get("validation") and not processed["validation"].get("valid", False):
        errors = processed["validation"].get("errors", [])
        error_msg = "; ".join(errors) if errors else "Transaction validation failed"
        logger.warning("[AGENT] Validation failed: %s", error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    record = db.add_transaction(processed)
    logger.info(
        "[AGENT] Transaction %s stored | confidence=%.2f | status=%s",
        record["id"], record["agent_confidence"], record["status"],
    )
    return _txn_to_response(record)


@app.get(
    "/api/transactions/search",
    response_model=List[TransactionResponse],
    tags=["Transactions"],
    summary="Search transactions by keyword",
)
def search_transactions(q: str = Query(..., min_length=1, description="Search keyword")):
    _log_request("GET", "/api/transactions/search")
    return [_txn_to_response(t) for t in db.search_transactions(q)]


@app.get(
    "/api/transactions/date-range",
    response_model=List[TransactionResponse],
    tags=["Transactions"],
    summary="Get transactions by date range",
)
def get_transactions_by_date_range(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    _log_request("GET", "/api/transactions/date-range")
    return [
        _txn_to_response(t)
        for t in db.get_transactions_by_date_range(start_date, end_date)
    ]


@app.get(
    "/api/transactions/category/{category}",
    response_model=List[TransactionResponse],
    tags=["Transactions"],
    summary="Get transactions by category",
)
def get_transactions_by_category(category: str):
    _log_request("GET", f"/api/transactions/category/{category}")
    return [_txn_to_response(t) for t in db.get_transactions_by_category(category)]


@app.get(
    "/api/transactions/status/{status}",
    response_model=List[TransactionResponse],
    tags=["Transactions"],
    summary="Get transactions by status",
)
def get_transactions_by_status(status: str):
    _log_request("GET", f"/api/transactions/status/{status}")
    return [_txn_to_response(t) for t in db.get_transactions_by_status(status)]


@app.get(
    "/api/transactions/all",
    response_model=List[TransactionResponse],
    tags=["Transactions"],
    summary="Get all transactions",
)
def list_transactions():
    _log_request("GET", "/api/transactions/all")
    return [_txn_to_response(t) for t in db.get_all_transactions()]


@app.get(
    "/api/transactions/stats",
    response_model=List[CategorySummary],
    tags=["Transactions"],
    summary="Get spending summary by category",
)
def transaction_stats():
    _log_request("GET", "/api/transactions/stats")
    return db.get_category_summary()


@app.get(
    "/api/transactions/{transaction_id}",
    response_model=TransactionResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["Transactions"],
    summary="Get a single transaction by ID",
)
def get_transaction(transaction_id: str):
    _log_request("GET", f"/api/transactions/{transaction_id}")
    txn = db.get_transaction_by_id(transaction_id)
    if txn is None:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    return _txn_to_response(txn)


@app.put(
    "/api/transactions/{transaction_id}",
    response_model=TransactionResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["Transactions"],
    summary="Update an existing transaction",
)
def update_transaction(transaction_id: str, payload: TransactionUpdate):
    _log_request("PUT", f"/api/transactions/{transaction_id}")
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = db.update_transaction(transaction_id, update_data)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    return _txn_to_response(updated)


@app.delete(
    "/api/transactions/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    tags=["Transactions"],
    summary="Delete a transaction",
)
def delete_transaction(transaction_id: str):
    _log_request("DELETE", f"/api/transactions/{transaction_id}")
    if not db.delete_transaction(transaction_id):
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    return None


# ─── Agent ───────────────────────────────────────────────────────────────────


@app.get(
    "/api/agent/status",
    response_model=AgentStateResponse,
    tags=["Agent"],
    summary="Get current agent state",
)
def agent_status():
    _log_request("GET", "/api/agent/status")
    state = agent.get_state()
    return AgentStateResponse(
        thinking_state=state["thinking_state"],
        current_cycle=state["current_cycle"],
        task_complete=state["task_complete"],
        error_count=state["error_count"],
        executed_actions=state["executed_actions"],
        memory_summary=state["memory_summary"],
    )


@app.post(
    "/api/agent/reset",
    response_model=MessageResponse,
    tags=["Agent"],
    summary="Reset agent to initial state",
)
def reset_agent():
    _log_request("POST", "/api/agent/reset")
    agent.reset()
    return {"message": "Agent reset successfully"}


# ─── Goals ────────────────────────────────────────────────────────────────────

goal_planner = GoalPlannerAgent()


@app.post("/api/goals", response_model=GoalSchema, tags=["Goals"])
async def create_new_goal(goal_data: GoalCreate):
    """
    Create a new financial goal

    Request body:
    {
        "user_id": "user123",
        "goal_name": "Emergency Fund",
        "goal_type": "long_term",
        "target_amount": 50000,
        "deadline": "2027-12-31T00:00:00",
        "priority": "high",
        "description": "6 months emergency fund"
    }
    """
    try:
        goal_dict = goal_data.model_dump()
        created_goal = create_goal(goal_data.user_id, goal_dict)
        return JSONResponse(status_code=201, content=created_goal)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/goals/{user_id}", tags=["Goals"])
async def get_goals(user_id: str):
    """
    Get all goals for a user

    Returns:
    {
        "user_id": "user123",
        "goals": [...],
        "total_goals": 5,
        "active_goals": 3,
        "completed_goals": 1
    }
    """
    try:
        goals = get_user_goals(user_id)
        if not goals:
            return {
                "user_id": user_id,
                "goals": [],
                "total_goals": 0,
                "active_goals": 0,
                "completed_goals": 0,
            }
        active = [g for g in goals if g.get("status") == "active"]
        completed = [g for g in goals if g.get("status") == "completed"]
        return {
            "user_id": user_id,
            "goals": goals,
            "total_goals": len(goals),
            "active_goals": len(active),
            "completed_goals": len(completed),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/goals/detail/{goal_id}", tags=["Goals"])
async def get_goal(goal_id: str):
    """
    Get single goal with progress details

    Returns:
    {
        "goal_id": "uuid...",
        "goal_name": "Emergency Fund",
        "target_amount": 50000,
        "current_amount": 10000,
        "progress_percentage": 20.0,
        ...
    }
    """
    try:
        goal = get_goal_by_id(goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        goal["progress_percentage"] = get_goal_progress_percentage(goal_id)
        return goal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/goals/{goal_id}", tags=["Goals"])
async def update_goal_route(goal_id: str, updates: dict):
    """
    Update goal fields

    Request body (any fields):
    {
        "goal_name": "New Goal Name",
        "priority": "medium",
        "status": "completed"
    }
    """
    try:
        updated = update_goal(goal_id, updates)
        if not updated:
            raise HTTPException(status_code=404, detail="Goal not found")
        updated["progress_percentage"] = get_goal_progress_percentage(goal_id)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/goals/{goal_id}", tags=["Goals"])
async def delete_goal_route(goal_id: str):
    """Delete a goal"""
    try:
        success = delete_goal(goal_id)
        if not success:
            raise HTTPException(status_code=404, detail="Goal not found")
        return {"status": "deleted", "goal_id": goal_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/goals/{goal_id}/add-progress", tags=["Goals"])
async def add_goal_progress(goal_id: str, amount_data: dict):
    """
    Add progress to goal (add savings)

    Request body:
    {
        "amount": 5000
    }
    """
    try:
        amount = amount_data.get("amount", 0)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        updated = add_to_goal(goal_id, amount)
        if not updated:
            raise HTTPException(status_code=404, detail="Goal not found")
        updated["progress_percentage"] = get_goal_progress_percentage(goal_id)
        return {
            "status": "success",
            "goal_id": goal_id,
            "amount_added": amount,
            "new_progress": updated["current_amount"],
            "progress_percentage": updated["progress_percentage"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/goals/analyze", tags=["Goals", "AI"])
async def analyze_goals(analyze_data: dict):
    """
    Run GoalPlanner Agent to analyze spending and suggest goals

    Request body:
    {
        "user_id": "user123",
        "monthly_income": 100000
    }
    """
    try:
        user_id = analyze_data.get("user_id")
        monthly_income = analyze_data.get("monthly_income", 0)
        if not user_id or monthly_income <= 0:
            raise HTTPException(status_code=400, detail="Invalid user_id or income")
        transactions = get_user_transactions(user_id)
        result = goal_planner.process_goal_request(
            user_id=user_id,
            goal_description=f"Plan goals with ${monthly_income} monthly income",
            transactions=transactions,
        )
        analysis = result.get("spending_analysis", {})
        savings_monthly = max(
            (analysis.get("avg_monthly", 0) - analysis.get("total_txns", 0) * 0.7)
            if analysis.get("total_txns", 0) > 0 else monthly_income * 0.2,
            0
        )
        return {
            "status": "analyzed",
            "user_id": user_id,
            "monthly_income": monthly_income,
            "spending_analysis": analysis,
            "savings_capacity": {"monthly_savable": round(savings_monthly, 2), "annual_potential": round(savings_monthly * 12, 2)},
            "suggested_goals": result.get("suggested_goals", []),
            "action_plans": result.get("action_plans", []),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Budgets ──────────────────────────────────────────────────────────────────

budget_monitor = BudgetMonitorAgent()


@app.post("/api/budgets", response_model=BudgetSchema, tags=["Budgets"])
async def create_new_budget(budget_data: BudgetCreate):
    """
    Create a new budget for a category

    Request body:
    {
        "user_id": "user123",
        "category": "Food",
        "monthly_limit": 15000,
        "month": "2026-07"
    }
    """
    try:
        budget_dict = budget_data.model_dump()
        created = create_budget(budget_data.user_id, budget_dict)
        return JSONResponse(status_code=201, content=created)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/budgets/{user_id}/{month}", tags=["Budgets"])
async def get_budgets_by_month(user_id: str, month: str):
    """
    Get all budgets for user in a specific month

    Format: month = "2026-07"

    Returns:
    {
        "user_id": "user123",
        "month": "2026-07",
        "budgets": [...],
        "total_limit": 50000,
        "total_spent": 40000,
        "total_remaining": 10000
    }
    """
    try:
        budgets = get_user_budgets_fn(user_id, month)
        if not budgets:
            return {
                "user_id": user_id,
                "month": month,
                "budgets": [],
                "total_limit": 0,
                "total_spent": 0,
                "total_remaining": 0,
            }
        total_limit = sum(b.get("monthly_limit", 0) for b in budgets)
        total_spent = sum(b.get("spent_so_far", 0) for b in budgets)
        total_remaining = total_limit - total_spent
        return {
            "user_id": user_id,
            "month": month,
            "budgets": budgets,
            "total_limit": total_limit,
            "total_spent": round(total_spent, 2),
            "total_remaining": round(total_remaining, 2),
            "overall_spent_percentage": round((total_spent / total_limit * 100) if total_limit > 0 else 0, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/budgets/{user_id}", tags=["Budgets"])
async def get_current_budgets(user_id: str):
    """Get current month's budgets for user"""
    current_month = datetime.now().strftime("%Y-%m")
    budgets = get_user_budgets_fn(user_id, current_month)
    if not budgets:
        return {
            "user_id": user_id,
            "month": current_month,
            "budgets": [],
            "total_limit": 0,
            "total_spent": 0,
            "total_remaining": 0,
        }
    total_limit = sum(b.get("monthly_limit", 0) for b in budgets)
    total_spent = sum(b.get("spent_so_far", 0) for b in budgets)
    total_remaining = total_limit - total_spent
    return {
        "user_id": user_id,
        "month": current_month,
        "budgets": budgets,
        "total_limit": total_limit,
        "total_spent": round(total_spent, 2),
        "total_remaining": round(total_remaining, 2),
        "overall_spent_percentage": round((total_spent / total_limit * 100) if total_limit > 0 else 0, 2),
    }


@app.get("/api/budgets/detail/{budget_id}", tags=["Budgets"])
async def get_budget(budget_id: str):
    """Get single budget with detailed status"""
    try:
        budget = get_budget_by_id(budget_id)
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        budget["spent_percentage"] = get_budget_spent_percentage(budget_id)
        pct = budget["spent_percentage"]
        if pct >= 100:
            budget["status"] = "exceeded"
        elif pct >= 80:
            budget["status"] = "warning"
        else:
            budget["status"] = "ok"
        return budget
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/budgets/{budget_id}", tags=["Budgets"])
async def update_budget_route(budget_id: str, updates: dict):
    """Update budget fields"""
    try:
        updated = update_budget(budget_id, updates)
        if not updated:
            raise HTTPException(status_code=404, detail="Budget not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/budgets/{budget_id}", tags=["Budgets"])
async def delete_budget_route(budget_id: str):
    """Delete a budget"""
    try:
        success = delete_budget(budget_id)
        if not success:
            raise HTTPException(status_code=404, detail="Budget not found")
        return {"status": "deleted", "budget_id": budget_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/budgets/{budget_id}/add-spending", tags=["Budgets"])
async def add_budget_spending(budget_id: str, spending_data: dict):
    """
    Add spending amount to budget

    Request body:
    {
        "amount": 1500,
        "description": "Groceries"
    }
    """
    try:
        amount = spending_data.get("amount", 0)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        updated = add_to_budget_spent(budget_id, amount)
        if not updated:
            raise HTTPException(status_code=404, detail="Budget not found")
        spent_pct = get_budget_spent_percentage(budget_id)
        pct = spent_pct
        if pct >= 100:
            budget_status = "exceeded"
        elif pct >= 80:
            budget_status = "warning"
        else:
            budget_status = "ok"
        return {
            "status": "success",
            "budget_id": budget_id,
            "amount_added": amount,
            "new_spent_total": updated["spent_so_far"],
            "spent_percentage": spent_pct,
            "budget_status": budget_status,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/budgets/check-alerts", tags=["Budgets"])
async def check_alerts(alert_data: dict):
    """
    Check budget alerts for user in a month

    Request body:
    {
        "user_id": "user123",
        "month": "2026-07"
    }
    """
    try:
        user_id = alert_data.get("user_id")
        month = alert_data.get("month")
        if not user_id or not month:
            raise HTTPException(status_code=400, detail="Missing user_id or month")
        alerts = check_budget_alerts(user_id, month)
        return {
            "status": "checked",
            "user_id": user_id,
            "month": month,
            "warnings": alerts.get("warnings", []),
            "critical": alerts.get("critical", []),
            "total_alerts": len(alerts.get("warnings", [])) + len(alerts.get("critical", [])),
            "summary": {
                "total_spent": alerts.get("total_spent", 0),
                "total_limit": alerts.get("total_limit", 0),
                "overall_percentage": round(
                    (alerts.get("total_spent", 0) / alerts.get("total_limit", 1)) * 100, 2
                ),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/budgets/monitor", tags=["Budgets", "AI"])
async def monitor_budgets(monitor_data: dict):
    """
    Run BudgetMonitor Agent for full budget analysis

    Request body:
    {
        "user_id": "user123",
        "month": "2026-07"
    }
    """
    try:
        user_id = monitor_data.get("user_id")
        month = monitor_data.get("month")
        if not user_id or not month:
            raise HTTPException(status_code=400, detail="Missing user_id or month")
        budgets = get_user_budgets_fn(user_id, month)
        transactions = get_user_transactions(user_id)
        if not budgets:
            raise HTTPException(status_code=404, detail="No budgets found for month")
        results = budget_monitor.monitor_user_budgets(user_id, budgets, transactions)
        thresholds = budget_monitor.check_all_thresholds(user_id, budgets, transactions)
        report = budget_monitor.generate_daily_report(user_id, budgets, transactions)
        realloc = budget_monitor.suggest_reallocations(user_id, budgets, transactions)
        return {
            "status": "monitored",
            "user_id": user_id,
            "month": month,
            "individual_results": results,
            "budget_status": {
                "total_budgets": len(budgets),
                "critical_count": thresholds.get("critical_count", 0),
                "warning_count": thresholds.get("warning_count", 0),
                "ok_count": thresholds.get("ok_count", 0),
            },
            "alerts": thresholds.get("alerts", []),
            "report": report,
            "suggested_adjustments": realloc.get("reallocations", []),
            "report_generated": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Health & Info ────────────────────────────────────────────────────────────


@app.get("/api/health", tags=["System"])
async def api_health_check():
    """Check API health"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.get("/api/info", tags=["System"])
async def api_info():
    """Get API information"""
    return {
        "name": "Personal Finance Tracker API",
        "version": "1.0.0",
        "phase": "3",
        "agents": {
            "goal_planner": "Active",
            "budget_monitor": "Active",
        },
        "database": "Mock (In-Memory)",
        "ai_model": "Google Gemini 2.5 Flash",
    }
