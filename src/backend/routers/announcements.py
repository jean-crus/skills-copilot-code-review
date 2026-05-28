"""
Announcement endpoints for the High School Management System API
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def parse_iso_date(raw_value: Optional[str], field_name: str) -> Optional[date]:
    """Parse an ISO date string and raise a validation error when invalid."""
    if raw_value in (None, ""):
        return None

    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must use YYYY-MM-DD format"
        ) from exc


def serialize_announcement(announcement: Dict[str, Any]) -> Dict[str, Any]:
    """Return API-safe announcement payload."""
    return {
        "id": announcement["_id"],
        "title": announcement["title"],
        "message": announcement["message"],
        "starts_at": announcement.get("starts_at"),
        "expires_at": announcement["expires_at"],
        "created_by": announcement.get("created_by"),
        "updated_by": announcement.get("updated_by")
    }


def validate_teacher(username: Optional[str]) -> Dict[str, Any]:
    """Validate the managing teacher/admin user."""
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Authentication required for this action"
        )

    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def validate_announcement_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate announcement fields and normalize the payload."""
    title = (payload.get("title") or "").strip()
    message = (payload.get("message") or "").strip()
    starts_at = parse_iso_date(payload.get("starts_at"), "starts_at")
    expires_at = parse_iso_date(payload.get("expires_at"), "expires_at")

    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    if not expires_at:
        raise HTTPException(status_code=400, detail="expires_at is required")

    if starts_at and starts_at > expires_at:
        raise HTTPException(
            status_code=400,
            detail="starts_at cannot be later than expires_at"
        )

    return {
        "title": title,
        "message": message,
        "starts_at": starts_at.isoformat() if starts_at else None,
        "expires_at": expires_at.isoformat()
    }


def build_active_query(today: date) -> Dict[str, Any]:
    """Build the query for announcements visible today."""
    return {
        "$and": [
            {
                "$or": [
                    {"starts_at": None},
                    {"starts_at": {"$exists": False}},
                    {"starts_at": {"$lte": today.isoformat()}}
                ]
            },
            {"expires_at": {"$gte": today.isoformat()}}
        ]
    }


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_announcements(
    include_all: bool = Query(False),
    teacher_username: Optional[str] = Query(None)
) -> List[Dict[str, Any]]:
    """Get active announcements for the public UI or all announcements for management."""
    if include_all:
        validate_teacher(teacher_username)

    query = {} if include_all else build_active_query(date.today())
    announcements = announcements_collection.find(query).sort([
        ("expires_at", 1),
        ("starts_at", 1),
        ("title", 1)
    ])
    return [serialize_announcement(announcement) for announcement in announcements]


@router.post("", response_model=Dict[str, Any], status_code=201)
@router.post("/", response_model=Dict[str, Any], status_code=201)
def create_announcement(
    teacher_username: Optional[str] = Query(None),
    payload: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Create a new announcement. Teacher authentication is required."""
    teacher = validate_teacher(teacher_username)
    normalized = validate_announcement_payload(payload)
    announcement_id = payload.get("id") or payload.get("title")
    normalized_id = "-".join(announcement_id.lower().split())

    if announcements_collection.find_one({"_id": normalized_id}):
        raise HTTPException(status_code=409, detail="Announcement already exists")

    document = {
        "_id": normalized_id,
        **normalized,
        "created_by": teacher["username"],
        "updated_by": teacher["username"]
    }
    announcements_collection.insert_one(document)
    return serialize_announcement(document)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None),
    payload: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Update an existing announcement. Teacher authentication is required."""
    teacher = validate_teacher(teacher_username)

    if not announcements_collection.find_one({"_id": announcement_id}):
        raise HTTPException(status_code=404, detail="Announcement not found")

    normalized = validate_announcement_payload(payload)
    normalized["updated_by"] = teacher["username"]

    announcements_collection.update_one(
        {"_id": announcement_id},
        {"$set": normalized}
    )

    updated = announcements_collection.find_one({"_id": announcement_id})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to load announcement")

    return serialize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
    """Delete an announcement. Teacher authentication is required."""
    validate_teacher(teacher_username)
    result = announcements_collection.delete_one({"_id": announcement_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted successfully"}