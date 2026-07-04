import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.database.mongo import get_db
from backend.agent import FinanceTrackerAgent, TransactionInput, TransactionUpdate as AgentTransactionUpdate
from backend.models.transaction import doc_to_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

agent = FinanceTrackerAgent()


class TransactionSearchResult(BaseModel):
    id: str = Field(..., alias="_id")
    amount: float
    category: str
    description: str
    date: str
    created_at: str = ""
    agent_confidence: float = 0.0
    status: str = "pending"

    class Config:
        populate_by_name = True


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_transaction(payload: TransactionInput):
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    db = await get_db()
    from bson.objectid import ObjectId
    doc = {
        "_id": ObjectId(),
        "user_id": "default",
        "amount": processed["amount"],
        "category": processed["category"],
        "description": processed["description"],
        "date": datetime.strptime(processed["date"], "%Y-%m-%d"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "agent_confidence": processed["agent_confidence"],
        "status": processed["status"],
        "agent_notes": "",
        "tags": [],
        "recurring": False,
        "recurring_frequency": "",
        "metadata": {
            "agent_reasoning": f"Validation: {processed.get('validation', {})}, Categorization: {processed.get('categorization', {})}",
            "original_category_suggestion": processed.get("categorization", {}).get("category", ""),
        },
    }
    await db["transactions"].insert_one(doc)

    from backend.cache.cache_manager import CacheManager
    CacheManager.invalidate_analytics("default")
    CacheManager.invalidate_forecast("default")

    logger.info("[AGENT] Transaction stored | confidence=%.2f | status=%s", processed["agent_confidence"], processed["status"])
    return doc_to_response(doc)


@router.get("/all")
async def list_transactions():
    db = await get_db()
    cursor = db["transactions"].find({"user_id": "default"}).sort("date", -1)
    docs = await cursor.to_list(length=None)
    return [doc_to_response(d) for d in docs]


@router.get("/search")
async def search_transactions(q: str = Query(..., min_length=1)):
    db = await get_db()
    import re as regex
    pattern = regex.compile(regex.escape(q), regex.IGNORECASE)
    cursor = db["transactions"].find({
        "user_id": "default",
        "$or": [{"description": pattern}, {"category": pattern}],
    }).sort("date", -1)
    docs = await cursor.to_list(length=None)
    return [doc_to_response(d) for d in docs]


@router.get("/date-range")
async def get_transactions_by_date_range(start_date: str = Query(...), end_date: str = Query(...)):
    db = await get_db()
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    cursor = db["transactions"].find({
        "user_id": "default",
        "date": {"$gte": start, "$lte": end},
    }).sort("date", -1)
    docs = await cursor.to_list(length=None)
    return [doc_to_response(d) for d in docs]


@router.get("/category/{category}")
async def get_transactions_by_category(category: str):
    db = await get_db()
    cursor = db["transactions"].find({"user_id": "default", "category": category}).sort("date", -1)
    docs = await cursor.to_list(length=None)
    return [doc_to_response(d) for d in docs]


@router.get("/status/{status}")
async def get_transactions_by_status(status: str):
    db = await get_db()
    cursor = db["transactions"].find({"user_id": "default", "status": status}).sort("date", -1)
    docs = await cursor.to_list(length=None)
    return [doc_to_response(d) for d in docs]


@router.get("/stats")
async def transaction_stats():
    db = await get_db()
    pipeline = [
        {"$match": {"user_id": "default"}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "total": {"$sum": "$amount"}}},
        {"$sort": {"total": -1}},
    ]
    results = await db["transactions"].aggregate(pipeline).to_list(length=None)
    return [{"category": r["_id"], "count": r["count"], "total": round(r["total"], 2)} for r in results]


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str):
    from bson.objectid import ObjectId
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    db = await get_db()
    doc = await db["transactions"].find_one({"_id": ObjectId(transaction_id), "user_id": "default"})
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    return doc_to_response(doc)


@router.put("/{transaction_id}")
async def update_transaction(transaction_id: str, payload: AgentTransactionUpdate):
    from bson.objectid import ObjectId
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.utcnow()
    if "date" in update_data:
        update_data["date"] = datetime.strptime(update_data["date"], "%Y-%m-%d")
    db = await get_db()
    result = await db["transactions"].find_one_and_update(
        {"_id": ObjectId(transaction_id), "user_id": "default"},
        {"$set": update_data},
        return_document=True,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    from backend.cache.cache_manager import CacheManager
    CacheManager.invalidate_analytics("default")
    return doc_to_response(result)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: str):
    from bson.objectid import ObjectId
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    db = await get_db()
    result = await db["transactions"].delete_one({"_id": ObjectId(transaction_id), "user_id": "default"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    from backend.cache.cache_manager import CacheManager
    CacheManager.invalidate_analytics("default")
    return None
