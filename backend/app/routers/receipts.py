from datetime import datetime, timezone
import io
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
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


def _sniff_content_type(data: bytes) -> str | None:
    """Return the content type the bytes actually are, or None (RCP-5)."""
    if data.startswith(JPEG_SIGNATURE):
        return "image/jpeg"
    if data.startswith(PNG_SIGNATURE):
        return "image/png"
    return None


def _get_owned_receipt(db: Session, current_user: User, receipt_id: str) -> Receipt | None:
    """RCP-3/RCP-12: nonexistent id, someone else's receipt, and a photoless
    lookup all produce the same not-found answer — deliberately no
    'not yours' signal."""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if receipt is None or receipt.user_id != current_user.id:
        return None
    return receipt


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


@router.post("/{receipt_id}/photo", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt_photo(
    receipt_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    receipt = _get_owned_receipt(db, current_user, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND_DETAIL)

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


@router.get("/{receipt_id}/photo")
def get_receipt_photo(
    receipt_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """RCP-2/RCP-3/RCP-12: serve the photo bytes to the owner only; every
    refusal is the same not-found."""
    receipt = _get_owned_receipt(db, current_user, receipt_id)
    if receipt is None or receipt.photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND_DETAIL)

    return Response(
        content=receipt.photo.data,
        media_type=receipt.photo.content_type,
        headers={"Cache-Control": "private, no-store"},
    )
