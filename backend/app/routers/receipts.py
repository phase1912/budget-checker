from datetime import datetime, timezone
import io
import os
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_active_user
from ..models import Receipt, ReceiptPhoto, User
from ..schemas import MessageResponse

router = APIRouter(prefix="/api/v1/receipts", tags=["receipts"])

# RCP-4 / INV-NFR-1: the size limit is a single named constant so it can come
# down (never the timeout up) if the bound-upload test fails. jpeg/png only,
# checked against the bytes, not the declared header (RCP-5).
MAX_PHOTO_SIZE_BYTES = int(os.environ.get("MAX_PHOTO_SIZE_BYTES", 5 * 1024 * 1024))
JPEG_SIGNATURE = b"\xff\xd8\xff"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

_NOT_FOUND_DETAIL = "Receipt not found"


class ReceiptCreate(BaseModel):
    """RCR-1: amount is required; description optional. Decimal (not float)
    so an over-precise amount survives parsing to be refused by rule
    (RCR-7) instead of being silently rounded. A client-supplied
    created_at or user_id is simply not a field here, so it is ignored."""

    amount: Decimal
    description: str | None = None


class ReceiptUpdate(BaseModel):
    """RCR-3: partial update — every field optional; only submitted fields
    apply. An explicit null description is indistinguishable from an omitted
    one under this schema (baseline open question 2: left alone either way)."""

    amount: Decimal | None = None
    description: str | None = None


def _sniff_content_type(data: bytes) -> str | None:
    """Return the content type the bytes actually are, or None (RCP-5)."""
    if data.startswith(JPEG_SIGNATURE):
        return "image/jpeg"
    if data.startswith(PNG_SIGNATURE):
        return "image/png"
    return None


def _check_amount(amount: Decimal) -> None:
    """RCR-7: refuse a negative or over-precise amount, naming the rule.
    More than two decimal places is over-precise for the Numeric(12, 2)
    column; no upper bound is checked in the router (the column's ceiling
    belongs to the database)."""
    if amount < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Amount must not be negative",
        )
    exponent = amount.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Amount must have at most two decimal places",
        )


def _get_owned_receipt(db: Session, current_user: User, receipt_id: str) -> Receipt | None:
    """RCP-3/RCP-12: nonexistent id, someone else's receipt, and a photoless
    lookup all produce the same not-found answer — deliberately no
    'not yours' signal."""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if receipt is None or receipt.user_id != current_user.id:
        return None
    return receipt


def _owned_receipt_or_404(db: Session, current_user: User, receipt_id: str) -> Receipt:
    """RCR-6: the uniform not-found every new endpoint answers with."""
    receipt = _get_owned_receipt(db, current_user, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND_DETAIL)
    return receipt


def _receipt_body(receipt: Receipt) -> dict:
    """RCR-2: the read-one body — id, amount as a number, description,
    creation time. Deliberately no has_photo (baseline open question 1)."""
    return {
        "id": receipt.id,
        "amount": float(receipt.amount),
        "description": receipt.description,
        "created_at": receipt.created_at,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_receipt(
    payload: ReceiptCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """RCR-1: create a receipt owned by the caller; id and created_at are
    the model's own defaults, never taken from the request."""
    _check_amount(payload.amount)
    receipt = Receipt(
        user_id=current_user.id,
        amount=payload.amount,
        description=payload.description,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return _receipt_body(receipt)


@router.get("", response_model=None)
def list_receipts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """RCP-8: the signed-in person's receipts, and only theirs."""
    receipts = (
        db.query(Receipt)
        .filter(Receipt.user_id == current_user.id)
        .order_by(Receipt.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "amount": float(r.amount),
            "description": r.description,
            "created_at": r.created_at,
            "has_photo": r.photo is not None,
        }
        for r in receipts
    ]


@router.get("/{receipt_id}")
def get_receipt(
    receipt_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """RCR-2/RCR-6: read one of the caller's own receipts."""
    receipt = _owned_receipt_or_404(db, current_user, receipt_id)
    return _receipt_body(receipt)


@router.get("/{receipt_id}/photo")
def get_receipt_photo(
    receipt_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """RCP-2/RCP-3/RCP-12: serve the photo bytes to the owner only; every
    refusal is the same not-found."""
    receipt = _owned_receipt_or_404(db, current_user, receipt_id)
    if receipt.photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND_DETAIL)

    return Response(
        content=receipt.photo.data,
        media_type=receipt.photo.content_type,
        headers={"Cache-Control": "private, no-store"},
    )


@router.patch("/{receipt_id}")
def update_receipt(
    receipt_id: str,
    payload: ReceiptUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """RCR-3/RCR-7: apply exactly the submitted changes; a field not
    submitted is left alone; a bad amount is refused without any change."""
    receipt = _owned_receipt_or_404(db, current_user, receipt_id)
    if payload.amount is not None:
        _check_amount(payload.amount)
        receipt.amount = payload.amount
    if payload.description is not None:
        receipt.description = payload.description
    db.commit()
    db.refresh(receipt)
    return _receipt_body(receipt)


@router.delete("/{receipt_id}", response_model=MessageResponse)
def delete_receipt(
    receipt_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """RCR-4/RCR-5/RCR-6: delete the caller's own receipt; the photo goes
    with it through the Receipt.photo cascade (models.py), exactly as the
    model-layer test test_deleting_receipt_takes_its_photo_with_it pins."""
    receipt = _owned_receipt_or_404(db, current_user, receipt_id)
    db.delete(receipt)
    db.commit()
    return MessageResponse(message="Receipt deleted")


@router.post("/{receipt_id}/photo", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt_photo(
    receipt_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    receipt = _owned_receipt_or_404(db, current_user, receipt_id)

    # RCP-15: one photo per receipt; the refusal names the rule.
    if receipt.photo is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This receipt already carries its one photo",
        )

    # RCP-10: the whole read + write is one transaction boundary; nothing is
    # stored unless every check below passes and the commit succeeds.
    data = await file.read()
    if len(data) > MAX_PHOTO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Photo is {len(data)} bytes; the limit is {MAX_PHOTO_SIZE_BYTES} bytes"
            ),
        )

    content_type = _sniff_content_type(data)
    if content_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only image/jpeg and image/png photos are accepted",
        )

    db.add(
        ReceiptPhoto(
            receipt_id=receipt.id, content_type=content_type, data=data
        )
    )
    db.commit()
    return MessageResponse(message="Photo attached")
