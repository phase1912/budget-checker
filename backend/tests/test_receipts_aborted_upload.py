import asyncio
import io

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import register_error_handling
from backend.app.models import Receipt, ReceiptPhoto
from backend.app.routers import auth, receipts

# RCP-10, the literal scenario: a photo upload CUT OFF PART WAY through the
# multipart transfer. backend/tests/test_receipts.py covers the equivalent
# transaction boundaries (a rejected check, an injected commit failure), but
# nothing that actually aborts mid-body. This file drives the ASGI app
# directly with a request whose body generator raises after yielding half the
# bytes — what a client disconnecting mid-upload does to the server: the
# multipart parser dies before the endpoint body can run to its commit.

# Same isolation rationale as backend/tests/test_receipts.py: a dedicated app
# instance (not the shared one from backend.app.main, whose get_db override
# would race on import order) and a file-backed sqlite shared with the
# request-handling thread.
engine = create_engine(
    "sqlite:///./test_receipts_abort.db", connect_args={"check_same_thread": False}
)

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

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"jpegbody" * 10
BOUNDARY = "testabortboundary"


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _multipart_body() -> bytes:
    return (
        f"--{BOUNDARY}\r\n"
        'Content-Disposition: form-data; name="file"; filename="r.jpg"\r\n'
        "Content-Type: image/jpeg\r\n"
        "\r\n"
    ).encode() + JPEG_BYTES + f"\r\n--{BOUNDARY}--\r\n".encode()


def _dying_body(body: bytes):
    """An ASGI request body that dies after half its bytes."""

    async def gen():
        yield body[: len(body) // 2]
        raise ConnectionResetError("client disconnected mid-upload")

    return gen()


def _register_login_and_make_receipt(email, amount, description):
    from fastapi.testclient import TestClient

    sync_client = TestClient(app)
    reg = sync_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "first_name": "Dee",
        },
    )
    assert reg.status_code == 201, reg.text
    token = sync_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = sync_client.get("/api/v1/auth/me", headers=headers).json()["id"]

    db = TestingSessionLocal()
    receipt = Receipt(user_id=user_id, amount=amount, description=description)
    db.add(receipt)
    db.commit()
    receipt_id = receipt.id
    db.close()
    return sync_client, headers, receipt_id


def _send_cut_off_request(receipt_id, headers):
    """POST the photo upload over ASGI with the aborting body.

    Returns (raised, response): `raised` is the exception the abort surfaced,
    if the transport propagated it; `response` is the error response the app
    sent instead, if the server converted the dying body into one. Starlette
    has done either across versions — the assertion that matters for RCP-10
    is the database state afterwards, which both branches let us check.
    """

    async def run():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            try:
                resp = await client.post(
                    f"/api/v1/receipts/{receipt_id}/photo",
                    content=_dying_body(_multipart_body()),
                    headers={
                        **headers,
                        "Content-Type": f"multipart/form-data; boundary={BOUNDARY}",
                    },
                )
            except ConnectionResetError:
                return "reset", None
            except httpx.RemoteProtocolError:
                return "protocol", None
            return None, resp

    return asyncio.run(run())


def _assert_nothing_stored(receipt_id, amount, description):
    """RCP-10's actual demand: nothing stored, receipt exactly as it was."""
    db = TestingSessionLocal()
    assert db.query(ReceiptPhoto).filter_by(receipt_id=receipt_id).count() == 0
    after = db.query(Receipt).filter_by(id=receipt_id).one()
    assert float(after.amount) == amount
    assert after.description == description
    db.close()


def test_upload_aborted_part_way_stores_nothing_and_leaves_receipt_unchanged():
    # RCP-10: the request body dies mid-multipart-transfer; nothing is stored
    # and the receipt row is exactly as it was. The abort may surface as a
    # propagated ConnectionResetError or as a 400 from Starlette's multipart
    # parser converting it — both mean the endpoint body never ran to commit.
    _, headers, receipt_id = _register_login_and_make_receipt(
        "dee@example.com", "12.50", "team lunch"
    )

    raised, response = _send_cut_off_request(receipt_id, headers)
    if raised is None:
        # The parser turned the dying body into an error response (a
        # 4xx-class MultiPartException) rather than propagating the reset.
        assert response is not None
        assert 400 <= response.status_code < 500, response.status_code

    _assert_nothing_stored(receipt_id, 12.50, "team lunch")


def test_cut_off_upload_then_normal_upload_succeeds():
    # The receipt that survived a cut-off upload is still attachable: the
    # aborted attempt left no photo row behind, so the one-photo rule
    # (RCP-15) is not tripped by debris from the failed request.
    sync_client, headers, receipt_id = _register_login_and_make_receipt(
        "pat@example.com", "9.00", "taxi"
    )

    _send_cut_off_request(receipt_id, headers)
    _assert_nothing_stored(receipt_id, 9.00, "taxi")

    resp = sync_client.post(
        f"/api/v1/receipts/{receipt_id}/photo",
        files={"file": ("r.jpg", io.BytesIO(JPEG_BYTES), "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    db = TestingSessionLocal()
    assert db.query(ReceiptPhoto).filter_by(receipt_id=receipt_id).count() == 1
    db.close()
