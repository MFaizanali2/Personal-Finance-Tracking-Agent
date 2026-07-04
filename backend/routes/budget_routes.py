import logging
from datetime import datetime

from bson.objectid import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.database.mongo import get_db
from backend.models.budget import BudgetInput, budget_doc_to_response, DEFAULT_BUDGET_CATEGORIES
from backend.analytics.forecaster import ForecasterAgent
from backend.cache.cache_manager import CacheManager
from agent.budget_monitor_agent import BudgetMonitorAgent as ReACTBudgetMonitorAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/budget", tags=["Budget"])


class CreateBudgetInput(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    monthly_limit: float = Field(..., gt=0)
    month: str = ""


class UpdateBudgetInput(BaseModel):
    monthly_limit: float = Field(..., gt=0)


class CheckAlertsInput(BaseModel):
    user_id: str = "default"


class MonitorInput(BaseModel):
    user_id: str = "default"


@router.post("/set")
async def set_budget(data: BudgetInput):
    db = await get_db()
    now = datetime.utcnow()
    total = sum(data.budgets.values())
    result = await db["budgets"].update_one(
        {"user_id": "default", "month": data.month},
        {"$set": {
            "budgets": data.budgets,
            "total_budget": total,
            "updated_at": now,
        }, "$setOnInsert": {
            "user_id": "default",
            "month": data.month,
            "created_at": now,
        }},
        upsert=True,
    )
    CacheManager.invalidate_budget("default")
    doc = await db["budgets"].find_one({"user_id": "default", "month": data.month})
    return {"status": "success", "budget": budget_doc_to_response(doc)}


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_budget(data: CreateBudgetInput):
    db = await get_db()
    month = data.month or datetime.utcnow().strftime("%Y-%m")
    now = datetime.utcnow()
    doc = {
        "user_id": "default",
        "month": month,
        "category": data.category,
        "monthly_limit": data.monthly_limit,
        "spent_so_far": 0,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["budgets"].insert_one(doc)
    doc["_id"] = result.inserted_id
    CacheManager.invalidate_budget("default")
    return {"status": "created", "budget": {**doc, "_id": str(doc["_id"])}}


@router.get("/current")
async def get_current_budget():
    month = datetime.utcnow().strftime("%Y-%m")
    cached = CacheManager.get_budget("default", month)
    if cached:
        return cached
    db = await get_db()
    doc = await db["budgets"].find_one({"user_id": "default", "month": month})
    if not doc:
        default_budget = {
            "month": month,
            "budgets": DEFAULT_BUDGET_CATEGORIES,
            "total_budget": sum(DEFAULT_BUDGET_CATEGORIES.values()),
        }
        return {"status": "not_set", "default": default_budget, "message": "No budget set for current month"}
    result = budget_doc_to_response(doc)
    CacheManager.set_budget("default", result, month)
    return {"status": "set", "budget": result}


@router.get("/user/{user_id}")
async def get_user_budgets(user_id: str):
    month = datetime.utcnow().strftime("%Y-%m")
    db = await get_db()
    cursor = db["budgets"].find({"user_id": user_id, "month": month}).sort("category", 1)
    docs = await cursor.to_list(length=None)
    return {"budgets": [{**d, "_id": str(d["_id"])} for d in docs], "month": month}


@router.get("/user/{user_id}/{month}")
async def get_user_budgets_by_month(user_id: str, month: str):
    if len(month) != 7 or month[4] != "-":
        raise HTTPException(status_code=422, detail="Invalid month format. Use YYYY-MM.")
    db = await get_db()
    cursor = db["budgets"].find({"user_id": user_id, "month": month}).sort("category", 1)
    docs = await cursor.to_list(length=None)
    return {"budgets": [{**d, "_id": str(d["_id"])} for d in docs], "month": month}


@router.get("/history")
async def get_budget_history():
    db = await get_db()
    cursor = db["budgets"].find({"user_id": "default"}).sort("month", -1)
    docs = await cursor.to_list(length=None)
    return {"budgets": [budget_doc_to_response(d) for d in docs]}


@router.get("/{budget_id}")
async def get_budget(budget_id: str):
    if not ObjectId.is_valid(budget_id):
        raise HTTPException(status_code=404, detail="Budget not found")
    db = await get_db()
    doc = await db["budgets"].find_one({"_id": ObjectId(budget_id), "user_id": "default"})
    if not doc:
        raise HTTPException(status_code=404, detail="Budget not found")
    doc["_id"] = str(doc["_id"])
    return doc


@router.put("/{budget_id}")
async def update_budget(budget_id: str, data: UpdateBudgetInput):
    if not ObjectId.is_valid(budget_id):
        raise HTTPException(status_code=404, detail="Budget not found")
    db = await get_db()
    doc = await db["budgets"].find_one_and_update(
        {"_id": ObjectId(budget_id), "user_id": "default"},
        {"$set": {"monthly_limit": data.monthly_limit, "updated_at": datetime.utcnow()}},
        return_document=True,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Budget not found")
    CacheManager.invalidate_budget("default")
    return {"status": "updated", "budget": {**doc, "_id": str(doc["_id"])}}


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(budget_id: str):
    if not ObjectId.is_valid(budget_id):
        raise HTTPException(status_code=404, detail="Budget not found")
    db = await get_db()
    result = await db["budgets"].delete_one({"_id": ObjectId(budget_id), "user_id": "default"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Budget not found")
    CacheManager.invalidate_budget("default")
    return None


@router.get("/vs-actual")
async def budget_vs_actual(month: str = None):
    from backend.analytics.analyzer import AnalyticsEngine
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")
    analyzer = AnalyticsEngine()
    result = await analyzer.get_budget_vs_actual(month)
    return result


@router.post("/suggest")
async def suggest_budget():
    forecaster = ForecasterAgent()
    result = await forecaster.suggest_budget_adjustments()
    return result


@router.post("/check-alerts")
async def check_budget_alerts(data: CheckAlertsInput):
    db = await get_db()
    month = datetime.utcnow().strftime("%Y-%m")
    budget_doc = await db["budgets"].find_one({"user_id": data.user_id, "month": month})
    if not budget_doc:
        return {"alerts": [], "total_spent": 0, "monthly_limit": 0, "message": "No budget set for current month"}
    budgets = budget_doc.get("budgets", {})
    cursor = db["transactions"].find({"user_id": data.user_id})
    transactions = await cursor.to_list(length=None)
    actuals = {}
    for t in transactions:
        cat = t.get("category", "Other")
        actuals[cat] = actuals.get(cat, 0) + t.get("amount", 0)

    total_limit = sum(budgets.values())
    total_spent = sum(actuals.values())
    alerts = []
    for cat, limit in budgets.items():
        spent = actuals.get(cat, 0)
        pct = round(spent / limit * 100, 1) if limit > 0 else 0
        if pct >= 80:
            severity = "critical" if pct >= 100 else "warning"
            alerts.append({
                "category": cat,
                "severity": severity,
                "message": f"{cat} at {pct}% (${spent:.0f}/${limit:.0f})",
                "spent": round(spent, 2),
                "limit": limit,
                "percentage": pct,
            })
    return {"alerts": alerts, "total_spent": round(total_spent, 2), "monthly_limit": round(total_limit, 2)}


@router.post("/monitor")
async def monitor_budgets(data: MonitorInput):
    try:
        db = await get_db()
        month = datetime.utcnow().strftime("%Y-%m")
        budget_doc = await db["budgets"].find_one({"user_id": data.user_id, "month": month})
        budgets = []
        transactions = []
        if budget_doc:
            budgets = [{"category": k, "monthly_limit": v} for k, v in budget_doc.get("budgets", {}).items()]
            cursor = db["transactions"].find({"user_id": data.user_id})
            transactions = await cursor.to_list(length=None)

        monitor = ReACTBudgetMonitorAgent()
        result = monitor.monitor_user_budgets(data.user_id, budgets, transactions)
        thresholds = monitor.check_all_thresholds(data.user_id, budgets, transactions)
        report = monitor.generate_daily_report(data.user_id, budgets, transactions)
        realloc = monitor.suggest_reallocations(data.user_id, budgets, transactions)

        return {
            "status_report": {"budgets_monitored": len(budgets), "report": report},
            "alerts": thresholds.get("alerts", []),
            "recommendations": realloc.get("reallocations", []),
        }
    except Exception as e:
        logger.error("BudgetMonitorAgent failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Budget monitoring failed: {str(e)}")
