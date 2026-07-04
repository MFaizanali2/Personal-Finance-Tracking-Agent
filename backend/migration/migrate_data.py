"""
Migration script: Move data from Phase 1 in-memory MockDatabase to MongoDB.
Usage: python -m backend.migration.migrate_data
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datetime import datetime
from backend.database.mongo import connect_db, close_db, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

IN_MEMORY_DATA = [
    {"amount": 45.50, "category": "Food", "description": "Grocery shopping at Walmart", "date": "2026-06-28", "status": "confirmed", "agent_confidence": 0.85},
    {"amount": 120.00, "category": "Transport", "description": "Uber rides this week", "date": "2026-06-27", "status": "confirmed", "agent_confidence": 0.78},
    {"amount": 15.99, "category": "Entertainment", "description": "Netflix monthly subscription", "date": "2026-06-26", "status": "confirmed", "agent_confidence": 0.92},
    {"amount": 250.00, "category": "Shopping", "description": "New clothes at H&M", "date": "2026-06-25", "status": "confirmed", "agent_confidence": 0.80},
    {"amount": 85.00, "category": "Utilities", "description": "Electric bill payment", "date": "2026-06-24", "status": "confirmed", "agent_confidence": 0.88},
    {"amount": 200.00, "category": "Medical", "description": "Doctor appointment", "date": "2026-06-23", "status": "confirmed", "agent_confidence": 0.76},
    {"amount": 1500.00, "category": "Rent", "description": "Monthly rent payment", "date": "2026-06-22", "status": "confirmed", "agent_confidence": 0.95},
    {"amount": 32.50, "category": "Food", "description": "Restaurant dinner", "date": "2026-06-21", "status": "pending", "agent_confidence": 0.65},
    {"amount": 5000.00, "category": "Shopping", "description": "New laptop purchase", "date": "2026-06-20", "status": "flagged", "agent_confidence": 0.45},
    {"amount": 75.00, "category": "Entertainment", "description": "Concert tickets", "date": "2026-06-19", "status": "pending", "agent_confidence": 0.55},
    {"amount": 55.00, "category": "Transport", "description": "Gas station fill up", "date": "2026-06-18", "status": "confirmed", "agent_confidence": 0.82},
    {"amount": 12.99, "category": "Entertainment", "description": "Spotify premium", "date": "2026-06-17", "status": "confirmed", "agent_confidence": 0.90},
    {"amount": 220.00, "category": "Utilities", "description": "Internet and phone bill", "date": "2026-06-16", "status": "confirmed", "agent_confidence": 0.87},
    {"amount": 89.99, "category": "Food", "description": "Weekly groceries", "date": "2026-06-15", "status": "confirmed", "agent_confidence": 0.81},
    {"amount": 40.00, "category": "Transport", "description": "Taxi fare to airport", "date": "2026-06-14", "status": "pending", "agent_confidence": 0.60},
]

BUDGET_DATA = {
    "month": "2026-06",
    "budgets": {"Food": 500, "Transport": 200, "Entertainment": 300, "Shopping": 400, "Utilities": 150, "Medical": 200, "Rent": 2000, "Other": 100},
    "total_budget": 3850,
}


async def migrate():
    logger.info("Starting data migration from in-memory to MongoDB...")
    try:
        db = await connect_db()
    except Exception as e:
        logger.error("Failed to connect to MongoDB: %s", e)
        logger.info("Make sure MongoDB is running on localhost:27017")
        return

    txns_collection = db["transactions"]
    budgets_collection = db["budgets"]

    existing = await txns_collection.count_documents({})
    if existing > 0:
        logger.warning("MongoDB already has %d transactions. Delete all first? (y/n)", existing)
        return

    count = 0
    for item in IN_MEMORY_DATA:
        doc = {
            "user_id": "default",
            "amount": item["amount"],
            "category": item["category"],
            "description": item["description"],
            "date": datetime.strptime(item["date"], "%Y-%m-%d"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "agent_confidence": item.get("agent_confidence", 0.5),
            "status": item.get("status", "pending"),
            "agent_notes": "",
            "tags": [],
            "recurring": False,
            "recurring_frequency": "",
            "metadata": {"agent_reasoning": "", "original_category_suggestion": ""},
        }
        await txns_collection.insert_one(doc)
        count += 1
        logger.info("  Migrated: %s | $%.2f | %s", item["description"], item["amount"], item["category"])

    budget_doc = {
        "user_id": "default",
        "month": BUDGET_DATA["month"],
        "budgets": BUDGET_DATA["budgets"],
        "total_budget": BUDGET_DATA["total_budget"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await budgets_collection.insert_one(budget_doc)
    logger.info("  Migrated budget for %s", BUDGET_DATA["month"])

    await close_db()
    logger.info("Migration complete: %d transactions + 1 budget migrated", count)


if __name__ == "__main__":
    asyncio.run(migrate())
