"""Backend tests for the receipt CRUD endpoints (RCR-1..RCR-8, RCR-NFR-2).

Extends the harness pattern of backend/tests/test_receipts.py with its own
app instance and its own file-backed sqlite (the TestClient serves requests
on another thread, so an in-memory database would not be shared with the
overridden get_db session), because that module owns test_receipts_unit.db.
"""

from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import register_error_handling
from backend.app.models import Receipt, ReceiptPhoto, User
from backend.app.routers import auth, receipts
from backend.app.security import create_access_token

engine = create_engine(
    "sqlite:///./test_receipts_crud.db", connect_args={"check_same_thread": False}
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
app.include_router(receipts.router)
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app, raise_server_exceptions=False)

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"jpegbody" * 10
NOT_EXISTENT_ID = "00000000-0000-0000-0000-000000000000"


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _register_and_login(email="sam@example.com"):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!", "first_name": "Sam"},
    )
    assert reg.status_code == 201, reg.text
    return reg.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _current_user_id(token):
    me = client.get("/api/v1/auth/me", headers=_headers(token))
    assert me.status_code == 200
    return me.json()["id"]


def _make_receipt(db, user_id, amount="12.50", description="team lunch"):
    receipt = Receipt(user_id=user_id, amount=amount, description=description)
    db.add(receipt)
    db.commit()
    return receipt


def _get_db_session():
    return TestingSessionLocal()


def _naive_utc_now() -> datetime:
    """The model's default is aware UTC (models.py `_now`), but sqlite stores
    datetimes naive, so the created_at that comes back over the API parses
    naive. Compare against naive UTC to keep the subtraction well-typed."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --- RCR-1: create ---------------------------------------------------------


def test_create_receipt_returns_body_and_row_exists():
    token = _register_and_login()
    before = _naive_utc_now()
    resp = client.post(
        "/api/v1/receipts",
        json={"amount": 12.50, "description": "lunch"},
        headers=_headers(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["amount"] == 12.50
    assert body["description"] == "lunch"
    assert body["id"] and isinstance(body["id"], str)
    created = datetime.fromisoformat(body["created_at"]).replace(tzinfo=None)
    assert abs((created - before).total_seconds()) < 60

    db = _get_db_session()
    row = db.query(Receipt).filter_by(id=body["id"]).one()
    assert row.user_id == _current_user_id(token)  # owned by the caller
    assert float(row.amount) == 12.50
    db.close()


def test_create_receipt_without_description_reads_back_null():
    # RCR-1: description omitted
    token = _register_and_login()
    resp = client.post(
        "/api/v1/receipts", json={"amount": 12.50}, headers=_headers(token)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["description"] is None

    got = client.get(f"/api/v1/receipts/{resp.json()['id']}", headers=_headers(token))
    assert got.json()["description"] is None


def test_created_receipt_appears_first_in_list_newest_first():
    # RCR-1 / RCR-8
    token = _register_and_login()
    db = _get_db_session()
    older = _make_receipt(db, _current_user_id(token), description="older")
    db.close()

    created = client.post(
        "/api/v1/receipts",
        json={"amount": 3.00, "description": "newest"},
        headers=_headers(token),
    ).json()

    items = client.get("/api/v1/receipts", headers=_headers(token)).json()
    assert items[0]["id"] == created["id"]
    assert items[1]["id"] == older.id
    assert items[0]["description"] == "newest"


def test_client_supplied_id_and_created_at_are_ignored():
    # baseline open question 6, resolved as "silently ignored": the create
    # handler simply has no such fields.
    token = _register_and_login()
    resp = client.post(
        "/api/v1/receipts",
        json={
            "amount": 5.00,
            "id": NOT_EXISTENT_ID,
            "created_at": "1999-01-01T00:00:00Z",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["id"] != NOT_EXISTENT_ID
    assert body["created_at"][:2] == "20"


# --- RCR-2: read one -------------------------------------------------------


def test_read_back_own_receipt():
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token), amount="12.50", description="lunch")
    db.close()

    resp = client.get(f"/api/v1/receipts/{receipt.id}", headers=_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == receipt.id
    assert body["amount"] == 12.50
    assert body["description"] == "lunch"
    assert body["created_at"]


# --- RCR-3: update ---------------------------------------------------------


def test_update_amount_leaves_everything_else():
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token), amount="12.50", description="lunch")
    db.close()

    before = client.get(f"/api/v1/receipts/{receipt.id}", headers=_headers(token)).json()
    resp = client.patch(
        f"/api/v1/receipts/{receipt.id}",
        json={"amount": 13.25},
        headers=_headers(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["amount"] == 13.25
    assert body["description"] == "lunch"
    assert body["id"] == receipt.id
    assert body["created_at"] == before["created_at"]  # created_at unchanged


def test_update_only_description_leaves_amount():
    # RCR-3: a field not submitted is left alone
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token), amount="12.50", description="lunch")
    db.close()

    resp = client.patch(
        f"/api/v1/receipts/{receipt.id}",
        json={"description": "dinner"},
        headers=_headers(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["description"] == "dinner"
    assert body["amount"] == 12.50


def test_empty_update_changes_nothing_and_returns_receipt():
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token), amount="12.50", description="lunch")
    db.close()

    resp = client.patch(f"/api/v1/receipts/{receipt.id}", json={}, headers=_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["amount"] == 12.50
    assert body["description"] == "lunch"


# --- RCR-4 / RCR-5: delete -------------------------------------------------


def test_delete_receipt_then_read_is_not_found():
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()

    resp = client.delete(f"/api/v1/receipts/{receipt.id}", headers=_headers(token))
    assert resp.status_code == 200, resp.text
    assert "message" in resp.json()

    got = client.get(f"/api/v1/receipts/{receipt.id}", headers=_headers(token))
    assert got.status_code == 404
    assert got.json()["detail"] == "Receipt not found"


def test_delete_receipt_takes_its_photo_with_it():
    # RCR-5 through the HTTP path
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.add(ReceiptPhoto(receipt_id=receipt.id, content_type="image/jpeg", data=JPEG_BYTES))
    db.commit()
    db.close()

    resp = client.delete(f"/api/v1/receipts/{receipt.id}", headers=_headers(token))
    assert resp.status_code == 200, resp.text

    got = client.get(f"/api/v1/receipts/{receipt.id}/photo", headers=_headers(token))
    assert got.status_code == 404

    db = _get_db_session()
    assert db.query(ReceiptPhoto).count() == 0
    db.close()


# --- RCR-6 / RCR-NFR-2: the uniform not-found ------------------------------


def _uniform_404_case_ids():
    dee = _register_and_login("u1@example.com")
    pat = _register_and_login("u2@example.com")
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(dee))
    db.close()
    client.delete(f"/api/v1/receipts/{receipt.id}", headers=_headers(dee))
    return dee, pat, receipt


@pytest.mark.parametrize("method,path_tail,json_body", [
    ("get", "", None),
    ("patch", "", {"description": "x"}),
    ("delete", "", None),
])
def test_missing_foreign_and_deleted_are_the_same_not_found(method, path_tail, json_body):
    dee, pat, receipt = _uniform_404_case_ids()

    def call(method_name, receipt_id, who):
        fn = getattr(client, method_name)
        kwargs = {"headers": _headers(who)}
        if json_body is not None:
            kwargs["json"] = json_body
        return fn(f"/api/v1/receipts/{receipt_id}{path_tail}", **kwargs)

    baseline_missing = call(method, NOT_EXISTENT_ID, dee)
    foreign = call(method, receipt.id, pat)
    deleted = call(method, receipt.id, dee)

    for resp in (foreign, deleted):
        assert resp.status_code == 404
        assert resp.status_code == baseline_missing.status_code
        assert resp.content == baseline_missing.content  # byte-identical body
        assert resp.headers["content-length"] == baseline_missing.headers["content-length"]


# --- RCR-7: amount validation ----------------------------------------------


@pytest.mark.parametrize("amount,why", [
    (-5.00, "negative"),
    (12.505, "two decimal places"),
])
def test_bad_amount_refused_on_create_and_nothing_created(amount, why):
    token = _register_and_login()
    resp = client.post(
        "/api/v1/receipts", json={"amount": amount}, headers=_headers(token)
    )
    assert resp.status_code == 422, resp.text
    assert why in resp.json()["detail"]

    db = _get_db_session()
    assert db.query(Receipt).count() == 0
    db.close()


@pytest.mark.parametrize("amount,why", [
    (-5.00, "negative"),
    (12.505, "two decimal places"),
])
def test_bad_amount_refused_on_update_and_nothing_changed(amount, why):
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token), amount="12.50")
    db.close()

    resp = client.patch(
        f"/api/v1/receipts/{receipt.id}",
        json={"amount": amount},
        headers=_headers(token),
    )
    assert resp.status_code == 422, resp.text
    assert why in resp.json()["detail"]

    db = _get_db_session()
    assert float(db.query(Receipt).filter_by(id=receipt.id).one().amount) == 12.50
    db.close()


def test_amount_boundaries_accepted():
    # 0 is not negative; two decimals is exactly the precision allowed.
    token = _register_and_login()
    for amount in (0, 0.01, 99999999999.99):
        resp = client.post(
            "/api/v1/receipts", json={"amount": amount}, headers=_headers(token)
        )
        assert resp.status_code == 201, resp.text


# --- RCR-8: the list endpoint answers as it always has ---------------------


def test_list_endpoint_shape_and_ordering_frozen():
    dee = _register_and_login("list@example.com")
    pat = _register_and_login("list2@example.com")
    db = _get_db_session()
    dee_receipt = _make_receipt(db, _current_user_id(dee), description="dee's")
    pat_receipt = _make_receipt(db, _current_user_id(pat), description="pat's")
    db.add(ReceiptPhoto(receipt_id=pat_receipt.id, content_type="image/png", data=JPEG_BYTES))
    db.commit()
    db.close()

    resp = client.get("/api/v1/receipts", headers=_headers(dee))
    assert resp.status_code == 200
    items = resp.json()
    assert [i["id"] for i in items] == [dee_receipt.id]  # only own, newest first
    entry = items[0]
    assert set(entry.keys()) == {"id", "amount", "description", "created_at", "has_photo"}
    assert isinstance(entry["amount"], float)
    assert entry["has_photo"] is False


# --- auth (baseline open question 7: the existing dependency carries it) ----


def test_unauthenticated_requests_refused():
    token = _register_and_login("auth@example.com")
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()

    assert client.post("/api/v1/receipts", json={"amount": 1.00}).status_code == 401
    assert client.get(f"/api/v1/receipts/{receipt.id}").status_code == 401
    assert client.patch(
        f"/api/v1/receipts/{receipt.id}", json={"amount": 2.00}
    ).status_code == 401
    assert client.delete(f"/api/v1/receipts/{receipt.id}").status_code == 401


def test_foreign_admin_gets_not_found_not_server_error():
    # mirrors test_non_owner_and_admin_get_not_found... in test_receipts.py,
    # on the new endpoints.
    dee = _register_and_login("adm1@example.com")
    db = _get_db_session()
    admin = User(email="adm@example.com", hashed_password="h", role="admin", is_active=True)
    db.add(admin)
    db.flush()
    receipt = _make_receipt(db, _current_user_id(dee))
    db.close()
    admin_headers = _headers(create_access_token({"sub": admin.id, "role": "admin"}))

    missing = client.get(f"/api/v1/receipts/{NOT_EXISTENT_ID}", headers=admin_headers)
    foreign = client.get(f"/api/v1/receipts/{receipt.id}", headers=admin_headers)
    assert foreign.status_code == 404
    assert foreign.content == missing.content
