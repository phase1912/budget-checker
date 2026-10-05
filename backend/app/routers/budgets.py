from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_active_user
from ..models import Budget, Receipt, User
from ..schemas import BudgetCreate, BudgetSummaryResponse

router = APIRouter(prefix="/api/v1/budgets", tags=["budgets"])

_NOT_FOUND_DETAIL = "No budget is set for this period"


def _parse_period(period: str) -> tuple[datetime, datetime]:
    """BUD-4/BUD-6: a period is a YYYY-MM month string. Returns the month's
    boundaries — first day at midnight UTC inclusive, first day of the next
    month at midnight UTC exclusive (December rolls to January of the next
    year). Malformed periods are refused with the rule named (BUD-6)."""
    parts = period.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Period must be a month string in the format YYYY-MM (for example 2025-03)",
        )
    try:
        year = int(parts[0])
        month = int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Period must be a month string in the format YYYY-MM (for example 2025-03)",
        )
    if not 1 <= month <= 12:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Period must be a month string in the format YYYY-MM (for example 2025-03)",
        )
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    end = datetime(next_year, next_month, 1, tzinfo=timezone.utc)
    return start, end


def _validate_target(target_amount: float) -> None:
    """BUD-7: a target must be greater than zero and have no more than two
    decimal places; the refusal names the accepted rule. Checked in the
    endpoint, not the schema: the app-wide RequestValidationError handler
    returns the generic 422 message, which names no rule."""
    rounded = round(target_amount, 2)
    if target_amount <= 0 or abs(target_amount - rounded) > 1e-9:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Target amount must be greater than zero with at most two decimal places",
        )


def _get_owned_budgets(db: Session, current_user: User, period: str) -> list[Budget]:
    """BUD-5/BUD-8: a period this user never set and another user's budget
    produce the same empty answer — deliberately no 'not yours' signal."""
    return (
        db.query(Budget)
        .filter(Budget.user_id == current_user.id, Budget.period == period)
        .order_by(Budget.created_at.desc(), Budget.id)
        .all()
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def set_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """BUD-1/BUD-2: store the target for this user and period; setting the
    same period again replaces the target so exactly one row remains."""
    _parse_period(payload.period)
    _validate_target(payload.target_amount)

    existing = (
        db.query(Budget)
        .filter(Budget.user_id == current_user.id, Budget.period == payload.period)
        .all()
    )
    for row in existing:
        db.delete(row)
    budget = Budget(
        user_id=current_user.id,
        period=payload.period,
        target_amount=payload.target_amount,
    )
    db.add(budget)
    db.commit()
    return {"period": budget.period, "target_amount": float(budget.target_amount)}


def _spent_in_period(db: Session, current_user: User, start: datetime, end: datetime) -> float:
    """BUD-3/BUD-4: sum this user's receipt amounts whose timestamp falls in
    [start, end) UTC. Filtered in Python, not SQL: SQLite stores
    DateTime(timezone=True) as strings, and a string comparison of stored
    values against a tz-aware bound is not a reliable ordering at the
    exclusive boundary. One user's receipts are few (concept stage: a plain
    Python-side filter is fine at this scale). A stored aware timestamp is
    converted to UTC first; a naive one is taken as UTC."""
    total = 0.0
    for r in db.query(Receipt).filter(Receipt.user_id == current_user.id).all():
        ts = r.created_at
        if ts is None:
            continue
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc)
        else:
            ts = ts.replace(tzinfo=timezone.utc)
        if start <= ts < end:
            total += float(r.amount)
    return total


@router.get("/{period}/summary", response_model=BudgetSummaryResponse)
def get_budget_summary(
    period: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """BUD-3: target, spent (this user's receipts inside the month, computed
    on the fly), remaining and whether spending is over the target. Over is
    strict: spent > target (baseline open question 6 — chosen as the plain
    reading of 'over', recorded as an assumption). BUD-10: duplicate rows are
    tolerated — the read is deterministic (newest row wins) and the
    duplication is indicated."""
    budgets = _get_owned_budgets(db, current_user, period)
    if not budgets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND_DETAIL)

    start, end = _parse_period(period)
    spent = _spent_in_period(db, current_user, start, end)
    target = float(budgets[0].target_amount)
    return BudgetSummaryResponse(
        period=period,
        target_amount=target,
        spent=spent,
        remaining=target - spent,
        over=spent > target,
        duplicate_rows=len(budgets) > 1,
    )
