"""Backend tests for the budgets feature (BUD-1…BUD-11).

Same harness pattern as test_receipts.py: a dedicated app instance with an
overridden get_db (a file-backed sqlite, since TestClient serves on another
thread), its own auth register/login helpers, and storage seeded directly
where the API cannot create the precondition (BUD-10 duplicate rows). The
receipts router is included too: BUD-9 asserts the budgets refusal is the
SAME as the receipts refusal, which requires both endpoints in one app.

Receipt.created_at is a DateTime(timezone=True) column, so seeded receipts
pass datetime objects — the ISO strings in the scenarios are parsed, never
inserted raw (SQLAlchemy's SQLite dialect rejects strings on that column).
"""

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import register_error_handling
from backend.app.models import Budget, Receipt, User
from backend.app.routers import auth, budgets, receipts
from backend.app.security import create_access_token

engine = create_engine(
    "sqlite:///./test_budgets_unit.db", connect_args={"check_same_thread": False}
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
register_error_handling(app)
app.include_router(auth.router)
app.include_router(budgets.router)
app.include_router(receipts.router)
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app, raise_server_exceptions=False)

PERIOD = "2025-03"


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _register_and_login(email="alex@example.com"):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!"},
    )
    assert reg.status_code == 201, reg.text
    return reg.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _current_user_id(token):
    me = client.get("/api/v1/auth/me", headers=_headers(token))
    assert me.status_code == 200
    return me.json()["id"]


def _set_budget(token, period=PERIOD, target="150.00"):
    return client.post(
        "/api/v1/budgets",
        json={"period": period, "target_amount": float(target)},
        headers=_headers(token),
    )


def _summary(token, period=PERIOD):
    return client.get(f"/api/v1/budgets/{period}/summary", headers=_headers(token))


def _make_receipt(token, amount, created_at):
    db = TestingSessionLocal()
    try:
        receipt = Receipt(
            user_id=_current_user_id(token),
            amount=amount,
            created_at=datetime.fromisoformat(created_at),
        )
        db.add(receipt)
        db.commit()
        return receipt
    finally:
        db.close()


# BUD-1 (+ BUD-11: the routes are reachable through the app, exercising
# create_app's include of the budgets router indirectly).
def test_set_budget_stores_it():
    token = _register_and_login()
    resp = _set_budget(token)
    assert resp.status_code == 201, resp.text
    body = _summary(token).json()
    assert body["target_amount"] == 150.00
    assert body["period"] == PERIOD


def test_summary_shows_spent_remaining_and_not_over():
    token = _register_and_login()
    _set_budget(token)
    _make_receipt(token, "90.00", "2025-03-15T12:00:00+00:00")
    body = _summary(token).json()
    assert body["spent"] == 90.00
    assert body["remaining"] == 60.00
    assert body["over"] is False


def test_over_target_month_is_shown_as_over():
    token = _register_and_login()
    _set_budget(token)
    _make_receipt(token, "175.50", "2025-03-20T08:00:00+00:00")
    body = _summary(token).json()
    assert body["spent"] == 175.50
    assert body["over"] is True
    assert body["remaining"] == pytest.approx(-25.50)


def test_month_boundary_receipts():
    token = _register_and_login()
    _set_budget(token)
    # inclusive lower bound: exactly midnight UTC on the 1st
    _make_receipt(token, "10.00", "2025-03-01T00:00:00+00:00")
    assert _summary(token).json()["spent"] == 10.00
    # inclusive/exclusive upper bound: exactly midnight UTC on 1 April is OUT
    _make_receipt(token, "20.00", "2025-04-01T00:00:00+00:00")
    assert _summary(token).json()["spent"] == 10.00
    # and a non-UTC offset timestamp normalised into the month counts
    _make_receipt(token, "5.00", "2025-03-31T23:30:00+02:00")
    assert _summary(token).json()["spent"] == 15.00


def test_december_period_uses_next_years_january_as_end():
    token = _register_and_login()
    _set_budget(token, period="2024-12")
    _make_receipt(token, "10.00", "2024-12-31T23:59:00+00:00")
    _make_receipt(token, "40.00", "2025-01-01T00:00:00+00:00")
    body = _summary(token, period="2024-12").json()
    assert body["spent"] == 10.00


def test_another_users_receipts_not_counted():
    token = _register_and_login()
    _set_budget(token)
    other = _register_and_login(email="priya@example.com")
    _make_receipt(other, "999.00", "2025-03-10T10:00:00+00:00")
    assert _summary(token).json()["spent"] == 0.00


def test_month_with_no_receipts_spends_zero():
    token = _register_and_login()
    _set_budget(token)
    body = _summary(token).json()
    assert body["spent"] == 0.00
    assert body["remaining"] == 150.00
    assert body["over"] is False


# BUD-2
def test_setting_same_period_again_replaces_target():
    token = _register_and_login()
    assert _set_budget(token, target="150.00").status_code == 201
    assert _set_budget(token, target="200.00").status_code == 201
    db = TestingSessionLocal()
    try:
        rows = db.query(Budget).all()
        assert len(rows) == 1
        assert float(rows[0].target_amount) == 200.00
    finally:
        db.close()
    assert _summary(token).json()["target_amount"] == 200.00


def test_re_setting_target_changes_over_flag():
    token = _register_and_login()
    _set_budget(token)
    _make_receipt(token, "175.50", "2025-03-10T10:00:00+00:00")
    assert _summary(token).json()["over"] is True
    _set_budget(token, target="200.00")
    assert _summary(token).json()["over"] is False


# BUD-5
def test_summary_for_period_with_no_budget_says_none_is_set():
    token = _register_and_login()
    resp = _summary(token)
    assert resp.status_code == 404
    assert "no budget" in resp.json()["detail"].lower()
    # and it is a named not-found, not an invented zero target
    assert "target_amount" not in resp.json()


# BUD-6
@pytest.mark.parametrize("period", ["2024-13", "24-01", "2024-00", "monthly"])
def test_malformed_period_refused_with_rule_named(period):
    token = _register_and_login()
    resp = _set_budget(token, period=period)
    assert resp.status_code == 422
    assert "YYYY-MM" in resp.json()["detail"]


# BUD-7
@pytest.mark.parametrize("amount", [-10.00, 0.00, 10.999])
def test_invalid_target_refused_with_rule_named(amount):
    token = _register_and_login()
    resp = _set_budget(token, target=str(amount))
    assert resp.status_code == 422
    assert "greater than zero" in resp.json()["detail"]
    assert "two decimal places" in resp.json()["detail"]


def test_target_with_exactly_two_decimals_accepted():
    token = _register_and_login()
    resp = _set_budget(token, target="10.99")
    assert resp.status_code == 201


# BUD-8
def test_another_users_budget_is_answered_same_as_no_budget():
    alex = _register_and_login()
    priya = _register_and_login(email="priya@example.com")
    _set_budget(priya)
    resp = _summary(alex)
    assert resp.status_code == 404
    assert "150.0" not in resp.text


# BUD-9
def test_unauthenticated_requests_refused_like_receipts():
    resp = _summary("nonsense-token")
    assert resp.status_code == 401
    receipts_resp = client.get(
        "/api/v1/receipts", headers={"Authorization": "Bearer nonsense-token"}
    )
    assert receipts_resp.status_code == 401
    assert resp.json()["detail"] == receipts_resp.json()["detail"]


# BUD-10 — duplicate rows cannot be created through the API (BUD-2 replaces),
# so storage is seeded directly.
def test_duplicate_rows_read_deterministically_and_indicated():
    token = _register_and_login()
    user_id = _current_user_id(token)
    db = TestingSessionLocal()
    try:
        db.add(Budget(user_id=user_id, period=PERIOD, target_amount="150.00"))
        db.add(Budget(user_id=user_id, period=PERIOD, target_amount="150.00"))
        db.commit()
    finally:
        db.close()
    first = _summary(token).json()
    second = _summary(token).json()
    assert first["target_amount"] == 150.00
    assert second["target_amount"] == first["target_amount"]
    assert first["duplicate_rows"] is True
    assert second["duplicate_rows"] is True
