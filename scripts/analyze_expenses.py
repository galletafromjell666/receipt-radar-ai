"""Month-by-month expense analysis + merchant->category hints for the LLM.

Read-only against the DB. Also writes data/category_hints.json which
src/utils.py folds into the extraction prompt.

Usage:
    uv run python -m scripts.analyze_expenses
    uv run python -m scripts.analyze_expenses --months 6 --top 20
    uv run python -m scripts.analyze_expenses --no-write-hints
    uv run python -m scripts.analyze_expenses --self-test
"""

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from src.database import get_db
from src.models import Category, Expense

load_dotenv()

HINTS_PATH = os.path.join("data", "category_hints.json")
EDITS_GRACE = timedelta(seconds=5)


def normalize_merchant(name):
    """Collapse case/whitespace so 'Amazon ' and 'amazon' group together."""
    return " ".join((name or "").strip().lower().split())


def month_key(dt, tz_offset):
    """Bucket by local month (dates are stored naive UTC)."""
    return (dt + timedelta(hours=tz_offset)).strftime("%Y-%m")


def build_report(
    rows,
    tz_offset,
    top=10,
    min_hint_count=2,
    min_ambiguous_count=3,
):
    """Pure aggregation over row dicts. Returns months, ambiguous, hints."""
    months = defaultdict(
        lambda: {
            "count": 0,
            "amount": 0.0,
            "categories": Counter(),
            "merchants": Counter(),
            "edits": 0,
        }
    )
    merchant_cats = defaultdict(Counter)
    merchant_names = defaultdict(Counter)
    other_count = 0

    for r in rows:
        m = months[month_key(r["date"], tz_offset)]
        m["count"] += 1
        m["amount"] += r["amount"] or 0.0
        m["categories"][r["category"]] += 1
        m["merchants"][r["merchant"] or "(unknown)"] += 1

        norm = normalize_merchant(r["merchant"])
        if norm:
            merchant_cats[norm][r["category"]] += 1
            merchant_names[norm][r["merchant"]] += 1

        if r["category"] == "Other":
            other_count += 1

        updated, created = r.get("updated_at"), r.get("created_at")
        if updated and created and updated > created + EDITS_GRACE:
            m["edits"] += 1

    ambiguous = {
        norm: dict(cats) for norm, cats in merchant_cats.items() if len(cats) > 1
    }
    ambiguous_merchants = []
    for norm, cats in merchant_cats.items():
        total = sum(cats.values())
        if len(cats) > 1 and total >= min_ambiguous_count:
            ambiguous_merchants.append(
                {
                    "merchant": merchant_names[norm].most_common(1)[0][0],
                    "categories": dict(cats.most_common()),
                    "count": total,
                }
            )
    ambiguous_merchants.sort(key=lambda a: -a["count"])

    hints = []
    for norm, cats in merchant_cats.items():
        total = sum(cats.values())
        # Multi-category names go to the ambiguous list instead, never a prior.
        if len(cats) > 1:
            continue
        category = cats.most_common(1)[0][0]
        if category == "Other":
            continue
        if total >= min_hint_count:
            hints.append(
                {
                    "merchant": merchant_names[norm].most_common(1)[0][0],
                    "category": category,
                    "count": total,
                }
            )
    hints.sort(key=lambda h: -h["count"])

    return {
        "months": dict(sorted(months.items())),
        "ambiguous": ambiguous,
        "other_count": other_count,
        "hints": hints[:top],
        "ambiguous_merchants": ambiguous_merchants[:top],
    }


def fetch_rows(db):
    query = (
        db.query(
            Expense.merchant,
            Expense.amount,
            Expense.date,
            Expense.created_at,
            Expense.updated_at,
            Category.name,
        )
        .join(Category, Expense.category_id == Category.id)
        .all()
    )
    return [
        {
            "merchant": merchant,
            "amount": amount,
            "date": date,
            "created_at": created_at,
            "updated_at": updated_at,
            "category": category,
        }
        for merchant, amount, date, created_at, updated_at, category in query
    ]


def print_report(report, top):
    for month, m in report["months"].items():
        print(f"\n=== {month} === {m['count']} expenses, {m['amount']:.2f}")
        if m["edits"]:
            print(f"  manually edited: {m['edits']}")
        print("  categories:")
        for cat, n in m["categories"].most_common():
            print(f"    {cat:<14} {n}")
        print("  top merchants:")
        for name, n in m["merchants"].most_common(top):
            print(f"    {name:<24} {n}")

    print(f"\n=== 'Other' fallbacks (LLM misses): {report['other_count']}")
    print(f"=== Ambiguous merchants (split categories): {len(report['ambiguous'])}")
    for norm, cats in report["ambiguous"].items():
        print(f"    {norm:<24} {cats}")


def write_hints(report):
    os.makedirs(os.path.dirname(HINTS_PATH), exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "merchant_hints": report["hints"],
        "ambiguous_merchants": report["ambiguous_merchants"],
    }
    with open(HINTS_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    print(
        f"\nwrote {len(report['hints'])} hints and "
        f"{len(report['ambiguous_merchants'])} ambiguous merchants to {HINTS_PATH}"
    )


def filter_months(rows, months):
    if not months:
        return rows
    keys = set()
    for r in rows:
        keys.add(r["date"].strftime("%Y-%m"))
    keep = sorted(keys)[-months:]
    return [r for r in rows if r["date"].strftime("%Y-%m") in keep]


def self_test():
    tz = -6
    jan = datetime(2026, 1, 15, 12, 0)
    rows = [
        # 2026-02-01 03:00 UTC is still Jan 31 local (tz -6) -> January bucket.
        {
            "merchant": "DeepSeek",
            "amount": 5.0,
            "date": datetime(2026, 2, 1, 3, 0),
            "created_at": jan,
            "updated_at": jan,
            "category": "Entertainment",
        },
        {
            "merchant": "DeepSeek",
            "amount": 7.0,
            "date": jan,
            "created_at": jan,
            "updated_at": jan,
            "category": "Entertainment",
        },
        # Split 1/1 -> ambiguous, never a hint regardless of counts.
        {
            "merchant": "Amazon",
            "amount": 20.0,
            "date": jan,
            "created_at": jan,
            "updated_at": jan,
            "category": "Shopping",
        },
        {
            "merchant": "amazon",
            "amount": 9.0,
            "date": jan,
            "created_at": jan,
            "updated_at": jan,
            "category": "Food",
        },
        # 3 rows -> eligible for the ambiguous list (>= min_ambiguous_count).
        {
            "merchant": "Split",
            "amount": 1.0,
            "date": jan,
            "created_at": jan,
            "updated_at": jan,
            "category": "Shopping",
        },
        {
            "merchant": "Split",
            "amount": 1.0,
            "date": jan,
            "created_at": jan,
            "updated_at": jan,
            "category": "Shopping",
        },
        {
            "merchant": "Split",
            "amount": 1.0,
            "date": jan,
            "created_at": jan,
            "updated_at": jan,
            "category": "Food",
        },
        # edited row: updated_at after created_at.
        {
            "merchant": "Netflix",
            "amount": 12.0,
            "date": jan,
            "created_at": jan,
            "updated_at": jan + timedelta(hours=1),
            "category": "Entertainment",
        },
        {
            "merchant": "Random",
            "amount": 3.0,
            "date": jan,
            "created_at": jan,
            "updated_at": jan,
            "category": "Other",
        },
    ]

    report = build_report(rows, tz, top=10)

    assert month_key(datetime(2026, 2, 1, 3, 0), tz) == "2026-01"
    assert month_key(datetime(2026, 2, 1, 7, 0), tz) == "2026-02"
    assert report["months"]["2026-01"]["count"] == 9
    assert report["months"]["2026-01"]["edits"] == 1
    assert report["other_count"] == 1
    assert "amazon" in report["ambiguous"]
    assert set(report["ambiguous"]["amazon"]) == {"Shopping", "Food"}

    amb_names = {a["merchant"] for a in report["ambiguous_merchants"]}
    assert "Split" in amb_names
    assert report["ambiguous_merchants"][0]["categories"] == {
        "Shopping": 2,
        "Food": 1,
    }
    # only 2 rows -> below min_ambiguous_count, kept out of the hint file
    assert "amazon" not in {n.lower() for n in amb_names}

    hint_merchants = {h["merchant"] for h in report["hints"]}
    assert "DeepSeek" in hint_merchants
    # single occurrence is below min_hint_count -> no hint
    assert "Netflix" not in hint_merchants
    # multi-category merchants are never a firm hint
    assert "Split" not in hint_merchants
    assert "amazon" not in {m.lower() for m in hint_merchants}
    assert "Random" not in hint_merchants
    assert report["hints"][0]["count"] == 2

    print("self-test ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--months", type=int, default=0, help="only the last N months (default: all)"
    )
    parser.add_argument(
        "--top", type=int, default=10, help="top merchants per month and hint cap"
    )
    parser.add_argument("--no-write-hints", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    tz_offset = int(os.getenv("TIMEZONE_OFFSET", "-6"))
    with next(get_db()) as db:
        rows = fetch_rows(db)

    rows = filter_months(rows, args.months)
    if not rows:
        print("No expenses found.")
        return

    report = build_report(rows, tz_offset, top=args.top)
    print_report(report, args.top)

    if not args.no_write_hints:
        write_hints(report)


if __name__ == "__main__":
    main()
