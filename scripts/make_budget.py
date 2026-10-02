"""Suggest a monthly budget per category from recent expenses.

Read-only against the DB, then asks DeepSeek for a monthly limit per active
category. Prints the result and writes Markdown to data/budgets/YYYY-MM-DD.md.

Usage:
    uv run python -m scripts.make_budget
    uv run python -m scripts.make_budget --days 120
    uv run python -m scripts.make_budget --cap 800
    uv run python -m scripts.make_budget --self-test
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from src.ai_service import suggest_budget
from src.database import get_db
from src.models import Category, Expense

load_dotenv()

BUDGETS_DIR = os.path.join("data", "budgets")


def fetch_expenses(db):
    """All expenses joined to their category name. Oldest rows included."""
    # ponytail: loads every row; push a date cutoff into SQL if it grows.
    query = (
        db.query(Expense.amount, Expense.date, Category.name)
        .join(Category, Expense.category_id == Category.id)
        .all()
    )
    return [
        {"amount": amount, "date": date, "category": category}
        for amount, date, category in query
    ]


def filter_window(rows, days, now):
    """Keep rows within the last `days` (dates are naive UTC)."""
    cutoff = now - timedelta(days=days)
    return [r for r in rows if r["date"] and r["date"] >= cutoff]


def build_budget_input(rows, category_names):
    """Aggregate spend per active category. Pure function."""
    totals = {name: {"total": 0.0, "count": 0} for name in category_names}
    for r in rows:
        if r["category"] not in totals:
            continue
        totals[r["category"]]["total"] += r["amount"] or 0.0
        totals[r["category"]]["count"] += 1
    grand = sum(t["total"] for t in totals.values())
    return [
        {
            "category": name,
            "total": totals[name]["total"],
            "count": totals[name]["count"],
            "avg_month": totals[name]["total"] / 3,
            "share": (totals[name]["total"] / grand) if grand else 0.0,
        }
        for name in category_names
    ]


def build_rows(budget_input, suggestions):
    """Merge LLM limits onto the input rows; fall back to the average."""
    known = {b["category"].lower() for b in budget_input}
    by_name = {}
    for s in suggestions.get("budgets", []):
        name = str(s.get("category", "")).strip().lower()
        if name not in known:
            bad = s.get("category")
            print(f"⚠️  ignoring unknown category '{bad}'", file=sys.stderr)
            continue
        by_name[name] = s

    rows = []
    for item in budget_input:
        s = by_name.get(item["category"].lower())
        if s is None:
            print(
                f"⚠️  LLM omitted '{item['category']}', using average.",
                file=sys.stderr,
            )
            limit, reason = item["avg_month"], "No LLM suggestion; 3-month average."
        else:
            try:
                limit = float(s.get("monthly_limit") or 0)
            except (TypeError, ValueError):
                limit = item["avg_month"]
            reason = str(s.get("reason") or "").strip()
        rows.append({**item, "limit": limit, "reason": reason})
    return rows


def delta(avg, limit):
    """Signed percentage change from average to limit ('—' when no average)."""
    if not avg:
        return "—"
    pct = (limit - avg) / avg
    if round(pct, 2) == 0:
        return "0%"
    return f"{pct:+.0%}"


def render_markdown(run_date, start, end, days, rows, cap=None):
    """Markdown report. Pure function."""
    total = sum(r["limit"] for r in rows)
    spent = sum(r["total"] for r in rows)
    count = sum(r["count"] for r in rows)
    ordered = sorted(rows, key=lambda r: (-r["limit"], r["category"]))
    shown = [r for r in ordered if r["total"] > 0 or r["limit"] > 0]

    lines = [f"# Budget — {run_date}", ""]
    window = f"Window: last {days} days ({start} → {end})"
    if cap:
        window += f" · cap {cap:,.2f}"
    lines += [window, ""]
    lines += [
        "| Category | Total | Share | Count | Avg/mo | Limit | vs avg |",
        "|----------|------:|------:|------:|-------:|------:|-------:|",
    ]
    for r in shown:
        lines.append(
            f"| {r['category']} | {r['total']:,.2f} | {r['share']:.0%} | "
            f"{r['count']} | {r['avg_month']:,.2f} | {r['limit']:,.2f} | "
            f"{delta(r['avg_month'], r['limit'])} |"
        )
    lines.append(
        f"| **Total** | **{spent:,.2f}** | **100%** | {count} |  | "
        f"**{total:,.2f}** | **{delta(spent / 3, total)}** |"
    )

    notes = []
    for r in shown:
        if r["avg_month"] > 0:
            move = (
                f"average {r['avg_month']:,.2f}/mo → limit {r['limit']:,.2f}/mo "
                f"({delta(r['avg_month'], r['limit'])})"
            )
        else:
            move = f"no spend → limit {r['limit']:,.2f}/mo"
        text = f"- {r['category']}: {move}."
        if r["reason"]:
            text += f" {r['reason']}"
        notes.append(text)
    if notes:
        lines += ["", "## Notes", ""] + notes
    return "\n".join(lines) + "\n"


def write_budget_file(markdown, run_date):
    os.makedirs(BUDGETS_DIR, exist_ok=True)
    path = os.path.join(BUDGETS_DIR, f"{run_date}.md")
    with open(path, "w") as f:
        f.write(markdown)
    return path


def self_test():
    now = datetime(2026, 9, 30, 12, 0)
    rows = [
        {"category": "Food", "amount": 100.0, "date": datetime(2026, 9, 1)},
        {"category": "Food", "amount": 50.0, "date": datetime(2026, 8, 1)},
        {"category": "Transport", "amount": 30.0, "date": datetime(2026, 7, 15)},
        # older than the window -> dropped
        {"category": "Food", "amount": 999.0, "date": datetime(2026, 1, 1)},
    ]
    window = filter_window(rows, 90, now)
    assert len(window) == 3, window
    # 2026-07-02 cutoff: the July 15 row is inside, the January row is not.

    data = build_budget_input(window, ["Food", "Transport", "Gifts"])
    by = {d["category"]: d for d in data}
    assert by["Food"]["total"] == 150.0
    assert by["Food"]["count"] == 2
    assert abs(by["Food"]["avg_month"] - 50.0) < 1e-9
    assert by["Transport"]["total"] == 30.0
    assert by["Gifts"]["total"] == 0.0
    assert by["Gifts"]["count"] == 0
    assert abs(by["Food"]["share"] - 150 / 180) < 1e-9
    assert abs(by["Transport"]["share"] - 30 / 180) < 1e-9
    assert by["Gifts"]["share"] == 0.0

    suggestions = {
        "budgets": [
            {"category": "food", "monthly_limit": 200, "reason": "r"},
            {"category": "Transport", "monthly_limit": 40, "reason": "t"},
            {"category": "Nonsense", "monthly_limit": 5, "reason": "x"},
        ]
    }
    out = build_rows(data, suggestions)
    by2 = {r["category"]: r for r in out}
    assert by2["Food"]["limit"] == 200.0  # case-insensitive match
    assert by2["Gifts"]["limit"] == 0.0  # omitted -> average (0)
    assert "Nonsense" not in by2

    md = render_markdown("2026-09-30", "2026-07-02", "2026-09-30", 90, out)
    assert "# Budget — 2026-09-30" in md
    assert "**240.00**" in md  # 200 + 40
    assert "| Food |" in md
    assert "vs avg" in md
    assert "83%" in md  # Food share of the 180 spent
    assert "+300%" in md  # Food average 50 -> limit 200
    assert "average 50.00/mo" in md

    assert delta(100, 100) == "0%"
    assert delta(100, 100.2) == "0%"  # rounds to zero, no "-0%"/"+0%"
    assert delta(100, 99.8) == "0%"
    assert delta(0, 5) == "—"
    assert delta(100, 150) == "+50%"

    capped = render_markdown("2026-09-30", "2026-07-02", "2026-09-30", 90, out, cap=800)
    assert "cap 800.00" in capped

    print("self-test ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument(
        "--cap", type=float, default=None, help="hard cap on the total budget"
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    tz_offset = int(os.getenv("TIMEZONE_OFFSET", "-6"))
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC, as stored

    with next(get_db()) as db:
        names = [
            c.name
            for c in db.query(Category)
            .filter(Category.is_active.is_(True))
            .order_by(Category.id)
            .all()
        ]
        if not names:
            print("❌ No active categories.")
            sys.exit(1)
        rows = fetch_expenses(db)

    window = filter_window(rows, args.days, now)
    if not window:
        print(f"No expenses in the last {args.days} days. Nothing to budget.")
        return

    data = build_budget_input(window, names)
    try:
        suggestions = suggest_budget(data, args.days, args.cap)
    except Exception as e:
        print(f"❌ LLM request failed: {e}")
        sys.exit(1)

    out = build_rows(data, suggestions)

    local = now + timedelta(hours=tz_offset)
    run_date = local.strftime("%Y-%m-%d")
    start = (local - timedelta(days=args.days)).strftime("%Y-%m-%d")
    markdown = render_markdown(run_date, start, run_date, args.days, out, args.cap)

    path = write_budget_file(markdown, run_date)
    print(markdown)
    print(f"📄 Wrote {path}")


if __name__ == "__main__":
    main()
