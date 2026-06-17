"""
Notification routes: list, mark read, clear all.
"""

from datetime import datetime

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


# ────────────────────────────────────────────────────────────
# GET /api/notifications
# ────────────────────────────────────────────────────────────
@notifications_bp.route("", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM notifications
           WHERE user_id = %s
           ORDER BY created_at DESC
           LIMIT 50""",
        (user_id,),
    )
    notifs = cursor.fetchall()

    unread_count = sum(1 for n in notifs if not n["is_read"])

    cursor.close()
    conn.close()

    result = []
    for n in notifs:
        result.append({
            "id": n["id"],
            "icon": n["icon"],
            "icon_color": n["icon_color"],
            "icon_bg": n["icon_bg"],
            "title": n["title"],
            "body": n["body"],
            "is_new": bool(n["is_new"]),
            "is_read": bool(n["is_read"]),
            "time": _relative_time(n["created_at"]),
            "created_at": n["created_at"].isoformat() if isinstance(n["created_at"], datetime) else str(n["created_at"]),
        })

    return jsonify({
        "notifications": result,
        "unread_count": unread_count,
    }), 200


# ────────────────────────────────────────────────────────────
# PUT /api/notifications/<id>/read
# ────────────────────────────────────────────────────────────
@notifications_bp.route("/<int:notif_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(notif_id):
    user_id = int(get_jwt_identity())

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
        (notif_id, user_id),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Notification marked as read."}), 200


# ────────────────────────────────────────────────────────────
# POST /api/notifications/clear
# ────────────────────────────────────────────────────────────
@notifications_bp.route("/clear", methods=["POST"])
@jwt_required()
def clear_all():
    user_id = int(get_jwt_identity())

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET is_read = 1, is_new = 0 WHERE user_id = %s",
        (user_id,),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "All notifications cleared."}), 200


# ────────────────────────────────────────────────────────────
# Helper
# ────────────────────────────────────────────────────────────
def _relative_time(dt):
    if not isinstance(dt, datetime):
        return str(dt)
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        m = int(seconds // 60)
        return f"{m}m ago"
    if seconds < 86400:
        h = int(seconds // 3600)
        return f"{h}h ago"
    if seconds < 172800:
        return "Yesterday"
    days = int(seconds // 86400)
    return f"{days}d ago"
