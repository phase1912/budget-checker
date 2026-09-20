import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import register_error_handling
from backend.app.routers import auth, receipts
from backend.app.models import Receipt, ReceiptPhoto, User
from backend.app.routers.receipts import MAX_PHOTO_SIZE_BYTES
from backend.app.security import create_access_token

# Backend tests for the receipt-photo feature (RCP-1…RCP-16, INV-NFR-2).
# Size values are parameterised around MAX_PHOTO_SIZE_BYTES, not hard-coded
# 5 MB (baseline open question 1: the limit may come down, never the timeout up).

# A file-backed sqlite: the TestClient serves requests on another thread, so
# an in-memory database would not be shared with the overridden get_db session.
engine = create_engine(
    "sqlite:///./test_receipts_unit.db", connect_args={"check_same_thread": False}
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# expire_on_commit=False: the tests read receipt.id and the receipt's columns
# after the session that wrote them has closed; the default (expire on commit)
# DetachedInstanceErrors on exactly that access, which is what broke the last
# run of this suite (gate finding#178).
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# A DEDICATED app instance, not the shared one from backend.app.main. Setting
# app.dependency_overrides[get_db] on the shared app at module level made the
# override a race on import order: whichever test module was imported last
# won, and test_auth inherited this module's file-backed (empty) engine and
# failed with 503 "no such table: users" (gate finding#178, build run). The
# routers resolve get_db per-app, so a private app is isolated by construction.
app = FastAPI()
register_error_handling(app)
app.include_router(auth.router)
app.include_router(receipts.router)
app.dependency_overrides[get_db] = override_get_db

# raise_server_exceptions=False so the RCP-11 test receives the 500/503
# response the app's error handling produces, rather than the raw exception.
client = TestClient(app, raise_server_exceptions=False)

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"jpegbody" * 10
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"pngbody" * 10
NOT_EXISTENT_ID = "00000000-0000-0000-0000-000000000000"


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _register_and_login(email="dee@example.com"):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!", "first_name": "Dee"},
    )
    assert reg.status_code == 201, reg.text
    return reg.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _make_receipt(db, user_id, amount="12.50", description="team lunch"):
    receipt = Receipt(user_id=user_id, amount=amount, description=description)
    db.add(receipt)
    db.commit()
    return receipt


def _current_user_id(token):
    me = client.get("/api/v1/auth/me", headers=_headers(token))
    assert me.status_code == 200
    return me.json()["id"]


def _get_db_session():
    return TestingSessionLocal()


def test_receipt_photos_table_created_and_receipts_untouched():
    # RCP-6/RCP-7: create_all on a DB with pre-existing receipts rows creates
    # receipt_photos and leaves the receipts table definition alone.
    from sqlalchemy import inspect

    db = _get_db_session()
    user = User(email="old@example.com", hashed_password="h")
    db.add(user)
    db.flush()
    _make_receipt(db, user.id, description="pre-feature receipt")
    db.close()

    Base.metadata.create_all(bind=engine)  # what create_app runs at startup

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "receipt_photos" in tables
    receipt_cols = {c["name"] for c in inspector.get_columns("receipts")}
    assert receipt_cols == {"id", "user_id", "amount", "description", "created_at"}

    db = _get_db_session()
    assert db.query(Receipt).count() == 1
    db.close()


def test_attach_photo_to_photoless_receipt():
    # RCP-1
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()

    resp = client.post(
        f"/api/v1/receipts/{receipt.id}/photo",
        files={"file": ("receipt.jpg", io.BytesIO(JPEG_BYTES), "image/jpeg")},
        headers=_headers(token),
    )
    assert resp.status_code == 201, resp.text

    db = _get_db_session()
    photo = db.query(ReceiptPhoto).filter_by(receipt_id=receipt.id).one()
    assert photo.data == JPEG_BYTES
    assert photo.content_type == "image/jpeg"
    db.close()


def test_reopen_photo_in_a_new_session_returns_identical_bytes():
    # RCP-2
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()
    client.post(
        f"/api/v1/receipts/{receipt.id}/photo",
        files={"file": ("r.jpg", io.BytesIO(JPEG_BYTES), "image/jpeg")},
        headers=_headers(token),
    )

    # a "later session": a fresh token from a fresh login
    new_token = client.post(
        "/api/v1/auth/login",
        json={"email": "dee@example.com", "password": "SecurePassword123!"},
    ).json()["access_token"]
    resp = client.get(f"/api/v1/receipts/{receipt.id}/photo", headers=_headers(new_token))
    assert resp.status_code == 200
    assert resp.content == JPEG_BYTES
    assert resp.headers["content-type"] == "image/jpeg"


def test_non_owner_and_admin_get_not_found_identical_to_nonexistent_id():
    # RCP-3, INV-NFR-2: every authenticated refusal is byte-identical to the
    # nonexistent-id case; an unauthenticated request is refused by the
    # existing auth dependency exactly as it would be for a nonexistent id.
    dee = _register_and_login()
    pat = _register_and_login("pat@example.com")
    db = _get_db_session()
    dee_id = _current_user_id(dee)
    admin = User(email="admin@example.com", hashed_password="h", role="admin", is_active=True)
    db.add(admin)
    db.flush()
    receipt = _make_receipt(db, dee_id)
    db.close()
    client.post(
        f"/api/v1/receipts/{receipt.id}/photo",
        files={"file": ("r.jpg", io.BytesIO(JPEG_BYTES), "image/jpeg")},
        headers=_headers(dee),
    )

    # the baseline refusals the others must be identical to
    not_found = client.get(
        f"/api/v1/receipts/{NOT_EXISTENT_ID}/photo", headers=_headers(dee)
    )
    assert not_found.status_code == 404
    unauthed_not_found = client.get(
        f"/api/v1/receipts/{NOT_EXISTENT_ID}/photo"
    )

    attempts = {
        "pat": client.get(f"/api/v1/receipts/{receipt.id}/photo", headers=_headers(pat)),
        "unauthenticated": client.get(f"/api/v1/receipts/{receipt.id}/photo"),
        "admin": client.get(
            f"/api/v1/receipts/{receipt.id}/photo",
            headers=_headers(create_access_token({"sub": admin.id, "role": "admin"})),
        ),
    }
    for name, resp in attempts.items():
        if name == "unauthenticated":
            assert resp.status_code == unauthed_not_found.status_code, name
            assert resp.content == unauthed_not_found.content, name
        else:
            assert resp.status_code == not_found.status_code, name
            assert resp.content == not_found.content, name
            assert resp.headers["content-type"] == not_found.headers["content-type"], name


def test_photoless_receipt_is_the_same_not_found_as_nonexistent():
    # RCP-12
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()

    photoless = client.get(f"/api/v1/receipts/{receipt.id}/photo", headers=_headers(token))
    nonexistent = client.get(
        f"/api/v1/receipts/{NOT_EXISTENT_ID}/photo", headers=_headers(token)
    )
    assert photoless.status_code == 404
    assert photoless.content == nonexistent.content
    assert photoless.headers["content-type"] == nonexistent.headers["content-type"]


@pytest.mark.parametrize(
    "over_by,expected",
    [(0, 201), (1, 413)],
)
def test_size_limit_boundary(over_by, expected):
    # RCP-4: exactly the limit accepted, one byte over refused, nothing stored.
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()

    body_len = MAX_PHOTO_SIZE_BYTES + over_by
    # payload of body_len bytes that is still a valid jpeg by signature
    data = b"\xff\xd8\xff" + b"\x00" * (body_len - 3)
    resp = client.post(
        f"/api/v1/receipts/{receipt.id}/photo",
        files={"file": ("big.jpg", io.BytesIO(data), "image/jpeg")},
        headers=_headers(token),
    )
    assert resp.status_code == expected, resp.text
    if expected == 413:
        assert str(body_len) in resp.json()["detail"]
        assert str(MAX_PHOTO_SIZE_BYTES) in resp.json()["detail"]
        db = _get_db_session()
        assert db.query(ReceiptPhoto).filter_by(receipt_id=receipt.id).count() == 0
        db.close()


def test_non_image_bytes_refused_even_when_declared_jpeg():
    # RCP-5
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()

    resp = client.post(
        f"/api/v1/receipts/{receipt.id}/photo",
        files={"file": ("lie.jpg", io.BytesIO(b"this is not an image at all"), "image/jpeg")},
        headers=_headers(token),
    )
    assert resp.status_code == 415
    db = _get_db_session()
    assert db.query(ReceiptPhoto).filter_by(receipt_id=receipt.id).count() == 0
    db.close()


def test_second_photo_refused_conflict_and_first_unchanged():
    # RCP-15
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()
    client.post(
        f"/api/v1/receipts/{receipt.id}/photo",
        files={"file": ("a.jpg", io.BytesIO(JPEG_BYTES), "image/jpeg")},
        headers=_headers(token),
    )
    resp = client.post(
        f"/api/v1/receipts/{receipt.id}/photo",
        files={"file": ("b.jpg", io.BytesIO(PNG_BYTES), "image/png")},
        headers=_headers(token),
    )
    assert resp.status_code == 409
    assert "photo" in resp.json()["detail"].lower()
    db = _get_db_session()
    photo = db.query(ReceiptPhoto).filter_by(receipt_id=receipt.id).one()
    assert photo.data == JPEG_BYTES
    db.close()


def test_deleting_receipt_takes_its_photo_with_it():
    # RCP-9
    db = _get_db_session()
    user = User(email="cascade@example.com", hashed_password="h")
    db.add(user)
    db.flush()
    receipt = _make_receipt(db, user.id)
    db.add(ReceiptPhoto(receipt_id=receipt.id, content_type="image/jpeg", data=JPEG_BYTES))
    db.commit()

    db.delete(receipt)
    db.commit()
    assert db.query(ReceiptPhoto).count() == 0
    db.close()


def test_deleting_user_takes_every_photo_with_it():
    # RCP-9 (user cascade, exercising the pre-existing User.receipts chain)
    db = _get_db_session()
    user = User(email="gone@example.com", hashed_password="h")
    db.add(user)
    db.flush()
    r1 = _make_receipt(db, user.id)
    r2 = _make_receipt(db, user.id)
    db.add(ReceiptPhoto(receipt_id=r1.id, content_type="image/jpeg", data=JPEG_BYTES))
    db.add(ReceiptPhoto(receipt_id=r2.id, content_type="image/png", data=PNG_BYTES))
    db.commit()

    db.delete(user)
    db.commit()
    assert db.query(ReceiptPhoto).count() == 0
    db.close()


def test_upload_failing_checks_stores_nothing_and_leaves_receipt_unchanged():
    # RCP-10: the whole upload is one transaction boundary — nothing is
    # committed unless every check passes and the commit succeeds.
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()

    resp = client.post(
        f"/api/v1/receipts/{receipt.id}/photo",
        files={"file": ("x.jpg", io.BytesIO(b"garbage"), "image/jpeg")},
        headers=_headers(token),
    )
    assert resp.status_code == 415
    db = _get_db_session()
    assert db.query(ReceiptPhoto).filter_by(receipt_id=receipt.id).count() == 0
    after = db.query(Receipt).filter_by(id=receipt.id).one()
    assert float(after.amount) == 12.50
    assert after.description == "team lunch"
    db.close()


def test_db_write_failure_during_upload_leaves_nothing_behind():
    # RCP-11: a failing photo insert rolls back with no orphaned row and the
    # receipt row unchanged.
    token = _register_and_login()
    db = _get_db_session()
    receipt = _make_receipt(db, _current_user_id(token))
    db.close()

    from unittest.mock import patch

    from sqlalchemy.orm.session import Session as SASession

    with patch.object(SASession, "commit", side_effect=Exception("db down")):
        resp = client.post(
            f"/api/v1/receipts/{receipt.id}/photo",
            files={"file": ("r.jpg", io.BytesIO(JPEG_BYTES), "image/jpeg")},
            headers=_headers(token),
        )
    assert resp.status_code in (500, 503)

    db = _get_db_session()
    assert db.query(ReceiptPhoto).filter_by(receipt_id=receipt.id).count() == 0
    after = db.query(Receipt).filter_by(id=receipt.id).one()
    assert float(after.amount) == 12.50
    db.close()


def test_list_receipts_returns_only_own_receipts_with_photo_flag():
    # RCP-8
    dee = _register_and_login()
    pat = _register_and_login("pat2@example.com")
    db = _get_db_session()
    dee_receipt = _make_receipt(db, _current_user_id(dee), description="dee's")
    pat_receipt = _make_receipt(db, _current_user_id(pat), description="pat's")
    db.add(ReceiptPhoto(receipt_id=pat_receipt.id, content_type="image/png", data=PNG_BYTES))
    db.commit()
    db.close()

    resp = client.get("/api/v1/receipts", headers=_headers(dee))
    assert resp.status_code == 200
    items = resp.json()
    assert [i["id"] for i in items] == [dee_receipt.id]
    assert items[0]["description"] == "dee's"
    assert items[0]["has_photo"] is False
