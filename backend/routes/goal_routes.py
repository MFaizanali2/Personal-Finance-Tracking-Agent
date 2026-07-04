import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel, Field

from backend.database.mongo import get_db
from backend.models.goal import GoalInput, GoalUpdate, goal_doc_to_response
from backend.analytics.goal_planner import GoalPlannerAgent
from agent.goal_planner_agent import GoalPlannerAgent as ReACTGoalPlannerAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/goals", tags=["Goals"])


class AddProgressInput(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to add to goal progress")


class AnalyzeGoalsInput(BaseModel):
    user_id: str = "default"
    spending_history: list = []
    preferences: str = ""


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_goal(data: GoalInput):
    db = await get_db()
    now = datetime.utcnow()
    try:
        deadline = datetime.strptime(data.deadline, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")
    if deadline <= now:
        raise HTTPException(status_code=422, detail="Deadline must be in the future")
    doc = {
        "user_id": "default",
        "name": data.name,
        "target_amount": data.target_amount,
        "current_amount": data.current_amount,
        "category": data.category,
        "deadline": deadline,
        "monthly_contribution": data.monthly_contribution,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    result = await db["goals"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return goal_doc_to_response(doc)


@router.get("/all")
async def list_goals():
    db = await get_db()
    cursor = db["goals"].find({"user_id": "default"}).sort("created_at", -1)
    docs = await cursor.to_list(length=None)
    return [goal_doc_to_response(d) for d in docs]


@router.get("/active")
async def list_active_goals():
    db = await get_db()
    cursor = db["goals"].find({"user_id": "default", "status": "active"}).sort("deadline", 1)
    docs = await cursor.to_list(length=None)
    return [goal_doc_to_response(d) for d in docs]


@router.get("/{goal_id}")
async def get_goal(goal_id: str):
    from bson.objectid import ObjectId
    if not ObjectId.is_valid(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    db = await get_db()
    doc = await db["goals"].find_one({"_id": ObjectId(goal_id), "user_id": "default"})
    if not doc:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal_doc_to_response(doc)


@router.put("/{goal_id}")
async def update_goal(goal_id: str, data: GoalUpdate):
    from bson.objectid import ObjectId
    if not ObjectId.is_valid(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    update["updated_at"] = datetime.utcnow()
    if "deadline" in update:
        try:
            update["deadline"] = datetime.strptime(update["deadline"], "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")
    db = await get_db()
    doc = await db["goals"].find_one_and_update(
        {"_id": ObjectId(goal_id), "user_id": "default"},
        {"$set": update},
        return_document=True,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Goal not found")

    from backend.cache.cache_manager import CacheManager
    CacheManager.clear_cache(f"goal_planner:{'default'}")

    if doc.get("current_amount", 0) >= doc["target_amount"] and doc.get("status") == "active":
        await db["goals"].update_one(
            {"_id": ObjectId(goal_id)},
            {"$set": {"status": "completed", "updated_at": datetime.utcnow()}},
        )
        doc["status"] = "completed"
    return goal_doc_to_response(doc)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(goal_id: str):
    from bson.objectid import ObjectId
    if not ObjectId.is_valid(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    db = await get_db()
    result = await db["goals"].delete_one({"_id": ObjectId(goal_id), "user_id": "default"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    return None


@router.get("/progress/summary")
async def goal_progress_summary():
    from backend.analytics.goal_planner import GoalPlannerAgent
    planner = GoalPlannerAgent()
    result = await planner.analyze_all_goals()
    return result


@router.post("/plan")
async def generate_goal_plan(goal_id: str):
    from backend.analytics.goal_planner import GoalPlannerAgent
    planner = GoalPlannerAgent()
    result = await planner.create_savings_plan(goal_id)
    return result


@router.post("/{goal_id}/add-progress")
async def add_goal_progress(goal_id: str, data: AddProgressInput):
    from bson.objectid import ObjectId
    if not ObjectId.is_valid(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    db = await get_db()
    doc = await db["goals"].find_one_and_update(
        {"_id": ObjectId(goal_id), "user_id": "default"},
        {"$inc": {"current_amount": data.amount}, "$set": {"updated_at": datetime.utcnow()}},
        return_document=True,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Goal not found")
    current = doc["current_amount"]
    target = doc["target_amount"]
    if current >= target and doc.get("status") == "active":
        await db["goals"].update_one(
            {"_id": ObjectId(goal_id)},
            {"$set": {"status": "completed", "updated_at": datetime.utcnow()}},
        )
        doc["status"] = "completed"
    return goal_doc_to_response(doc)


@router.post("/analyze")
async def analyze_goals(data: AnalyzeGoalsInput):
    try:
        planner = ReACTGoalPlannerAgent()
        result = planner.process_goal_request(
            user_id=data.user_id,
            goal_description=data.preferences or "Help me set financial goals",
            transactions=data.spending_history,
        )
        suggestions = result.get("suggested_goals", [])
        action_plans = result.get("action_plans", [])
        analysis = result.get("spending_analysis", {})
        return {
            "recommended_goals": suggestions,
            "action_plans": action_plans,
            "spending_analysis": analysis,
            "user_id": data.user_id,
        }
    except Exception as e:
        logger.error("GoalPlannerAgent failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Goal analysis failed: {str(e)}")
