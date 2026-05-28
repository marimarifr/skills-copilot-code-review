"""
Announcement endpoints for the High School Management System API
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def _parse_iso_date(raw_value: Optional[str], field_name: str, required: bool) -> Optional[date]:
    """Parse YYYY-MM-DD strings to date, optionally requiring value."""
    if raw_value in (None, ""):
        if required:
            raise HTTPException(status_code=400, detail=f"{field_name} is required")
        return None

    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be in YYYY-MM-DD format"
        ) from exc


def _serialize_announcement(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Map Mongo document to API response shape."""
    return {
        "id": str(doc["_id"]),
        "message": doc.get("message", ""),
        "starts_on": doc.get("starts_on"),
        "expires_on": doc.get("expires_on"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at")
    }


def _require_authenticated_user(teacher_username: Optional[str]) -> Dict[str, Any]:
    """Validate that teacher_username maps to an existing logged-in teacher/admin."""
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """
    Get currently active announcements.

    Active means:
    - expires_on is today or in the future
    - starts_on is empty or starts_on is today or in the past
    """
    today = date.today()
    active_announcements: List[Dict[str, Any]] = []

    for doc in announcements_collection.find().sort("expires_on", 1):
        starts_on = _parse_iso_date(doc.get("starts_on"), "starts_on", required=False)
        expires_on = _parse_iso_date(doc.get("expires_on"), "expires_on", required=True)

        if expires_on < today:
            continue
        if starts_on and starts_on > today:
            continue

        active_announcements.append(_serialize_announcement(doc))

    return active_announcements


@router.get("/all", response_model=List[Dict[str, Any]])
def list_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """List all announcements for management. Requires authenticated teacher/admin."""
    _require_authenticated_user(teacher_username)

    announcements: List[Dict[str, Any]] = []
    for doc in announcements_collection.find().sort("expires_on", 1):
        announcements.append(_serialize_announcement(doc))

    return announcements


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    message: str,
    expires_on: str,
    starts_on: Optional[str] = None,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Create a new announcement. Requires authenticated teacher/admin.

    - message: announcement text
    - expires_on: required date (YYYY-MM-DD)
    - starts_on: optional date (YYYY-MM-DD)
    """
    _require_authenticated_user(teacher_username)

    sanitized_message = (message or "").strip()
    if not sanitized_message:
        raise HTTPException(status_code=400, detail="message is required")

    parsed_starts_on = _parse_iso_date(starts_on, "starts_on", required=False)
    parsed_expires_on = _parse_iso_date(expires_on, "expires_on", required=True)

    if parsed_starts_on and parsed_expires_on < parsed_starts_on:
        raise HTTPException(status_code=400, detail="expires_on must be on or after starts_on")

    timestamp = datetime.utcnow().isoformat()
    insert_doc = {
        "message": sanitized_message,
        "starts_on": parsed_starts_on.isoformat() if parsed_starts_on else None,
        "expires_on": parsed_expires_on.isoformat(),
        "created_at": timestamp,
        "updated_at": timestamp
    }

    result = announcements_collection.insert_one(insert_doc)
    created_doc = announcements_collection.find_one({"_id": result.inserted_id})

    if not created_doc:
        raise HTTPException(status_code=500, detail="Failed to create announcement")

    return _serialize_announcement(created_doc)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    message: str,
    expires_on: str,
    starts_on: Optional[str] = None,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Update an existing announcement. Requires authenticated teacher/admin.

    - message: announcement text
    - expires_on: required date (YYYY-MM-DD)
    - starts_on: optional date (YYYY-MM-DD)
    """
    _require_authenticated_user(teacher_username)

    try:
        from bson import ObjectId
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    existing_doc = announcements_collection.find_one({"_id": object_id})
    if not existing_doc:
        raise HTTPException(status_code=404, detail="Announcement not found")

    sanitized_message = (message or "").strip()
    if not sanitized_message:
        raise HTTPException(status_code=400, detail="message is required")

    parsed_starts_on = _parse_iso_date(starts_on, "starts_on", required=False)
    parsed_expires_on = _parse_iso_date(expires_on, "expires_on", required=True)

    if parsed_starts_on and parsed_expires_on < parsed_starts_on:
        raise HTTPException(status_code=400, detail="expires_on must be on or after starts_on")

    updated_doc = {
        "message": sanitized_message,
        "starts_on": parsed_starts_on.isoformat() if parsed_starts_on else None,
        "expires_on": parsed_expires_on.isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    result = announcements_collection.update_one(
        {"_id": object_id},
        {"$set": updated_doc}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    refreshed_doc = announcements_collection.find_one({"_id": object_id})
    if not refreshed_doc:
        raise HTTPException(status_code=500, detail="Failed to read updated announcement")

    return _serialize_announcement(refreshed_doc)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
    """Delete an announcement. Requires authenticated teacher/admin."""
    _require_authenticated_user(teacher_username)

    try:
        from bson import ObjectId
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    result = announcements_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted successfully"}
