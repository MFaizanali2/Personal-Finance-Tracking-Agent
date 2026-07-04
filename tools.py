import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

VALID_CATEGORIES: List[str] = [
    "Food", "Rent", "Transport", "Entertainment",
    "Medical", "Shopping", "Utilities", "Other",
]

DATE_FORMATS: List[str] = [
    "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d", "%d/%m/%Y",
    "%Y.%m.%d", "%d.%m.%Y", "%m-%d-%Y", "%Y%m%d",
]

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Food": [
        "restaurant", "groceries", "food", "lunch", "dinner",
        "breakfast", "cafe", "coffee", "supermarket", "pizza",
        "deli", "bakery", "takeout", "delivery", "snack",
    ],
    "Rent": ["rent", "lease", "rental", "housing", "mortgage", "deposit"],
    "Transport": [
        "gas", "fuel", "uber", "lyft", "taxi", "bus", "train",
        "metro", "parking", "toll", "gasoline", "subway",
    ],
    "Entertainment": [
        "movie", "netflix", "spotify", "concert", "game",
        "theatre", "streaming", "subscription", "hulu",
        "disney", "hbo", "cinema", "music", "ticket",
    ],
    "Medical": [
        "doctor", "hospital", "pharmacy", "clinic", "medicine",
        "health", "dentist", "insurance", "prescription",
        "optometrist", "therapy", "medical",
    ],
    "Shopping": [
        "amazon", "walmart", "clothes", "electronics", "store",
        "mall", "online", "target", "best buy", "costco",
    ],
    "Utilities": [
        "electricity", "electric", "water", "internet", "phone", "gas bill",
        "utility", "broadband", "power", "sewage", "trash",
    ],
}


def _parse_date(date_str: str) -> Optional[datetime]:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def validate_transaction(
    amount: float,
    category: str,
    date: str,
) -> Dict[str, Any]:
    errors: List[str] = []

    if not isinstance(amount, (int, float)):
        errors.append("Amount must be a number")
    elif amount <= 0:
        errors.append("Amount must be greater than 0")

    if not category or not isinstance(category, str):
        errors.append("Category must be a non-empty string")
    elif category not in VALID_CATEGORIES:
        errors.append(f"Category must be one of: {', '.join(VALID_CATEGORIES)}")

    date_parsed: Optional[datetime] = _parse_date(date)
    if date_parsed is None:
        errors.append("Invalid date format. Use YYYY-MM-DD or similar standard format")

    is_valid = len(errors) == 0
    confidence = 1.0 if is_valid else max(0.1, 1.0 - (len(errors) * 0.3))

    return {
        "valid": is_valid,
        "confidence": round(confidence, 2),
        "errors": errors if errors else None,
        "parsed_date": date_parsed.isoformat() if date_parsed else None,
    }


def categorize_expense(description: str) -> Dict[str, Any]:
    if not description or not isinstance(description, str):
        return {"category": "Other", "confidence": 0.5}

    desc_lower = description.lower()
    best_category = "Other"
    best_score = 0.0

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0.0
        for keyword in keywords:
            if keyword in desc_lower:
                score += 1.0
            pattern = r"\b" + re.escape(keyword.rstrip("s")) + r"\w*\b"
            matches = re.findall(pattern, desc_lower)
            score += len(matches) * 0.5

        if score > best_score:
            best_score = score
            best_category = category

    confidence = min(1.0, best_score / 3.0) if best_score > 0 else 0.5

    return {
        "category": best_category,
        "confidence": round(confidence, 2),
        "description": description,
    }


def _safe_amount(txn: Dict[str, Any]) -> float:
    try:
        return float(txn.get("amount", 0))
    except (ValueError, TypeError):
        return 0.0


def _safe_category(txn: Dict[str, Any]) -> str:
    cat = txn.get("category", "Other")
    return cat if cat in VALID_CATEGORIES else "Other"


def generate_summary(transactions_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not transactions_list:
        return {
            "total_transactions": 0,
            "total_amount": 0.0,
            "average_amount": 0.0,
            "by_category": [],
            "largest_transaction": None,
            "smallest_transaction": None,
            "date_range": None,
        }

    total_amount = 0.0
    category_totals: Dict[str, float] = {}
    category_counts: Dict[str, int] = {}
    dates: List[str] = []

    for txn in transactions_list:
        amount = _safe_amount(txn)
        category = _safe_category(txn)

        total_amount += amount
        category_totals[category] = category_totals.get(category, 0) + amount
        category_counts[category] = category_counts.get(category, 0) + 1

        if "date" in txn and txn["date"]:
            dates.append(str(txn["date"]))

    by_category = [
        {
            "category": cat,
            "count": category_counts.get(cat, 0),
            "total": round(category_totals.get(cat, 0), 2),
        }
        for cat in sorted(category_totals)
    ]

    by_category_sorted = sorted(by_category, key=lambda x: x["total"], reverse=True)

    safe_txns = [t for t in transactions_list if _safe_amount(t) > 0]
    largest = max(safe_txns, key=_safe_amount) if safe_txns else None
    smallest = min(transactions_list, key=_safe_amount) if transactions_list else None

    date_range: Optional[Dict[str, Optional[str]]] = None
    if dates:
        try:
            parsed = [d for d in dates if _parse_date(d)]
            if parsed:
                parsed.sort()
                date_range = {"from": parsed[0], "to": parsed[-1]}
        except Exception:
            date_range = None

    summary = {
        "total_transactions": len(transactions_list),
        "total_amount": round(total_amount, 2),
        "average_amount": round(total_amount / len(transactions_list), 2),
        "by_category": by_category_sorted,
        "largest_transaction": largest,
        "smallest_transaction": smallest,
        "date_range": date_range,
    }

    return summary
