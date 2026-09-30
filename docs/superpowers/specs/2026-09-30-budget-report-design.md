# Budget Report from 90-Day History — Design

Date: 2026-09-30
Status: approved for planning

## Goal

Add a read-only CLI that produces a suggested **monthly budget per category**
from the last 90 days of expenses, using the same active-category list already
sent to the LLM during extraction. The budget is printed to stdout **and**
written to a dated Markdown file. No database changes.

## Non-goals (YAGNI)

- No `budgets` table, no persistence, no actual-vs-budget tracking.
- No manual overrides of LLM limits.
- No scheduling; it is a script like the others in `scripts/`.

Add these when actual-vs-budget comparison is actually needed.

## Command

```bash
uv run python -m scripts.make_budget              # 90-day window
uv run python -m scripts.make_budget --days 120
uv run python -m scripts.make_budget --self-test
```

Exit non-zero on API/DB failure so a cron wrapper can detect it.

## Data flow

1. **`fetch_recent_expenses(db, days)`** — join `expenses` → `categories`,
   keep rows with `date >= utcnow - days`. Dates are stored naive UTC, so the
   cutoff is computed in UTC and compared directly. Reuses the join pattern
   from `scripts/analyze_expenses.fetch_rows`.

2. **`build_budget_input(rows, active_category_names)`** — pure function.
   For each active category returns:
   - `total` — sum of amounts over the window
   - `count` — number of expenses
   - `avg_month` — `total / 3` (90 days ≈ 3 months)

   Every active category is included; categories with no spend appear with
   `total = 0`, `count = 0`, `avg_month = 0`.

3. **`get_budget_prompt(budget_input, days)`** in `src/utils.py` — builds the
   prompt. Sends the category list and per-category numbers, asks for JSON:
   ```json
   {
     "budgets": [
       {"category": "Food", "monthly_limit": 250.0, "reason": "one short line"}
     ]
   }
   ```
   Instruction: the limit is a *monthly* target per category, anchored on
   `avg_month`, rounded sensibly. Categories may get `0` if unused. The grand
   total is computed by summing the limits, not requested from the LLM.

4. **`suggest_budget(budget_input, days)`** in `src/ai_service.py` — calls the
   existing DeepSeek client with `response_format={"type": "json_object"}` and
   returns the parsed dict. Mirrors `extract_expense_from_email`.

5. **`render_markdown(...)`** — pure function returning the Markdown string
   (see below).

6. **`write_budget_file(markdown, run_date)`** — writes to
   `data/budgets/YYYY-MM-DD.md`, creating the directory if needed.
   `run_date` is the **local** date (using `TIMEZONE_OFFSET`), since a budget
   is about local spending. Re-running the same day overwrites the file.

7. Print the same table to stdout.

## Output format

Filename: `data/budgets/2026-09-30.md` (local run date, `YYYY-MM-DD`).

```markdown
# Budget — 2026-09-30

Window: last 90 days (2026-07-02 → 2026-09-30)

| Category | 90-day total | Count | Avg/mo | Suggested limit |
|----------|-------------:|------:|-------:|----------------:|
| Food     |       612.50 |    48 | 204.17 |          200.00 |
| ...      |              |       |        |                 |
| **Total**|              |       |        |      **1,234.00** |  ← sum of limits

## Notes

- Food: anchored on avg, trimmed 2% toward the round number.
- ...
```

Numbers formatted to 2 decimals; total row bold. The `Notes` section holds the
LLM's one-line reason per category that has spend.

## Edge cases

- **No expenses in window** → print a message and exit 0 without calling the
  LLM (do not ask it to budget all-zeros).
- **Unknown category from the LLM** → warn on stderr and ignore that row;
  fall back to the computed `avg_month` for any active category the LLM omits.
- **Mixed currencies** → amounts summed as-is. Known limitation, consistent
  with the rest of the codebase.
- **API/DB failure** → print the error, exit non-zero.

## Testing

`--self-test` exercises the pure functions on fixed rows, no framework:

- window cutoff excludes rows older than `days`
- per-category `total`, `count`, `avg_month`
- zero-spend categories present with zeros
- `render_markdown` contains the total row and the given filename date

Mirrors `scripts/analyze_expenses.self_test`.

## Files

- **new** `scripts/make_budget.py`
- **edit** `src/ai_service.py` — add `suggest_budget`
- **edit** `src/utils.py` — add `get_budget_prompt`
- **edit** `scripts/README.md` — document the new script
