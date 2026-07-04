"""
Seed script: Populate MongoDB with 55 diverse transactions for testing.
Usage: python -m backend.seed_data
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from random import choice, randint, uniform

from backend.database.mongo import connect_db, close_db, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Utilities", "Medical", "Rent", "Other"]

TRANSACTION_TEMPLATES = [
    # Food (12)
    ("Grocery shopping at Walmart", "Food"),
    ("Restaurant dinner with friends", "Food"),
    ("Coffee shop latte and pastry", "Food"),
    ("Weekly groceries at Trader Joe's", "Food"),
    ("Lunch delivery from Uber Eats", "Food"),
    ("Sushi dinner at Sakura", "Food"),
    ("Farmers market vegetables", "Food"),
    ("Bakery fresh bread and croissants", "Food"),
    ("Pizza delivery Friday night", "Food"),
    ("Costco bulk grocery haul", "Food"),
    ("Brunch at the diner", "Food"),
    ("Ice cream shop dessert", "Food"),
    # Transport (8)
    ("Gas station fill up", "Transport"),
    ("Uber ride to airport", "Transport"),
    ("Monthly subway pass", "Transport"),
    ("Lyft ride downtown", "Transport"),
    ("Train ticket to NYC", "Transport"),
    ("Parking garage fee", "Transport"),
    ("Car wash and detailing", "Transport"),
    ("Bus pass monthly renewal", "Transport"),
    # Entertainment (8)
    ("Netflix monthly subscription", "Entertainment"),
    ("Spotify premium membership", "Entertainment"),
    ("Movie tickets with popcorn", "Entertainment"),
    ("Concert tickets - Rock Band", "Entertainment"),
    ("HBO Max streaming service", "Entertainment"),
    ("Bowling night with friends", "Entertainment"),
    ("Video game purchase", "Entertainment"),
    ("Theater play tickets", "Entertainment"),
    # Shopping (8)
    ("New running shoes", "Shopping"),
    ("Amazon electronics order", "Shopping"),
    ("Winter jacket sale", "Shopping"),
    ("Home decor from Target", "Shopping"),
    ("Smartwatch accessory", "Shopping"),
    ("Office supplies bundle", "Shopping"),
    ("Designer sunglasses", "Shopping"),
    ("Books from online store", "Shopping"),
    # Utilities (5)
    ("Electric bill payment", "Utilities"),
    ("Internet and phone bill", "Utilities"),
    ("Water utility charge", "Utilities"),
    ("Gas bill for heating", "Utilities"),
    ("Trash collection service", "Utilities"),
    # Medical (5)
    ("Doctor consultation fee", "Medical"),
    ("Pharmacy prescription", "Medical"),
    ("Dental checkup copay", "Medical"),
    ("Eye exam and glasses", "Medical"),
    ("Health insurance premium", "Medical"),
    # Rent (4)
    ("Monthly rent payment", "Rent"),
    ("Rent for June 2026", "Rent"),
    ("Security deposit refund", "Rent"),
    ("Rent for July 2026", "Rent"),
    # Other (5)
    ("ATM withdrawal fee", "Other"),
    ("Charity donation", "Other"),
    ("Bank service charge", "Other"),
    ("Gift for friend birthday", "Other"),
    ("Miscellaneous supplies", "Other"),
]

STATUSES = ["confirmed", "confirmed", "confirmed", "pending", "flagged"]


def generate_transactions(count: int = 55) -> list[dict]:
    now = datetime.utcnow()
    transactions = []
    for i in range(count):
        template, category = TRANSACTION_TEMPLATES[i % len(TRANSACTION_TEMPLATES)]
        days_ago = randint(0, 89)
        txn_date = now - timedelta(days=days_ago, hours=randint(0, 23), minutes=randint(0, 59))
        if category == "Rent":
            amount = round(uniform(1400, 2200), 2)
        elif category == "Food":
            amount = round(uniform(8, 250), 2)
        elif category == "Transport":
            amount = round(uniform(5, 150), 2)
        elif category == "Entertainment":
            amount = round(uniform(5, 200), 2)
        elif category == "Shopping":
            amount = round(uniform(10, 500), 2)
        elif category == "Utilities":
            amount = round(uniform(40, 300), 2)
        elif category == "Medical":
            amount = round(uniform(20, 400), 2)
        else:
            amount = round(uniform(5, 100), 2)
        agent_conf = round(uniform(0.45, 0.95), 2)
        if amount > 5000:
            status = "flagged"
        elif agent_conf < 0.5:
            status = "pending"
        elif amount > 2000:
            status = choice(["confirmed", "flagged", "pending"])
        else:
            status = choice(STATUSES)
        transactions.append({
            "user_id": "default",
            "amount": amount,
            "category": category,
            "description": template,
            "date": txn_date,
            "created_at": txn_date,
            "updated_at": txn_date,
            "agent_confidence": agent_conf,
            "status": status,
            "agent_notes": f"Auto-seeded transaction #{i+1}",
            "tags": [category.lower()],
            "recurring": True if template in ("Netflix monthly subscription", "Spotify premium membership", "Monthly subway pass", "Internet and phone bill") else False,
            "recurring_frequency": "monthly" if template in ("Netflix monthly subscription", "Spotify premium membership", "Monthly subway pass", "Internet and phone bill") else "",
            "metadata": {"agent_reasoning": f"Seeded via bulk import. Category: {category}", "original_category_suggestion": category},
        })
    return transactions


async def seed():
    try:
        await connect_db()
    except Exception as e:
        logger.error("Failed to connect to MongoDB: %s", e)
        return

    db = await get_db()
    existing = await db["transactions"].count_documents({"user_id": "default"})
    if existing > 0:
        logger.warning("Database already has %d transactions. Delete first? (y/n)", existing)
        resp = input("Delete existing data? (y/n): ").strip().lower()
        if resp == "y":
            await db["transactions"].delete_many({"user_id": "default"})
            await db["budgets"].delete_many({"user_id": "default"})
            await db["alerts"].delete_many({"user_id": "default"})
            logger.info("Existing data cleared")
        else:
            logger.info("Seeding cancelled")
            await close_db()
            return

    transactions = generate_transactions(55)

    # Add 3 more high-value flagged transactions for analytics richness
    transactions.extend([
        {"user_id": "default", "amount": 12000.00, "category": "Shopping", "description": "Luxury watch purchase", "date": datetime.utcnow() - timedelta(days=5), "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(), "agent_confidence": 0.35, "status": "flagged", "agent_notes": "High value flagged", "tags": ["shopping", "luxury"], "recurring": False, "recurring_frequency": "", "metadata": {"agent_reasoning": "High-value transaction flagged", "original_category_suggestion": "Shopping"}},
        {"user_id": "default", "amount": 8500.00, "category": "Entertainment", "description": "Vacation package booking", "date": datetime.utcnow() - timedelta(days=12), "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(), "agent_confidence": 0.40, "status": "flagged", "agent_notes": "High value flagged", "tags": ["entertainment", "travel"], "recurring": False, "recurring_frequency": "", "metadata": {"agent_reasoning": "High-value transaction flagged", "original_category_suggestion": "Entertainment"}},
        {"user_id": "default", "amount": 3200.00, "category": "Medical", "description": "Emergency room visit", "date": datetime.utcnow() - timedelta(days=20), "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(), "agent_confidence": 0.55, "status": "pending", "agent_notes": "Unusually high medical expense", "tags": ["medical", "emergency"], "recurring": False, "recurring_frequency": "", "metadata": {"agent_reasoning": "High medical expense - pending review", "original_category_suggestion": "Medical"}},
    ])

    await db["transactions"].insert_many(transactions)

    # Seed a budget
    budget_doc = {
        "user_id": "default",
        "month": datetime.utcnow().strftime("%Y-%m"),
        "budgets": {"Food": 600, "Transport": 250, "Entertainment": 300, "Shopping": 500, "Utilities": 200, "Medical": 300, "Rent": 2000, "Other": 150},
        "total_budget": 4300,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await db["budgets"].update_one(
        {"user_id": "default", "month": budget_doc["month"]},
        {"$set": budget_doc},
        upsert=True,
    )

    await close_db()
    logger.info("Seeded %d transactions + budget for %s", len(transactions), budget_doc["month"])


if __name__ == "__main__":
    asyncio.run(seed())
