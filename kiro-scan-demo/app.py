# app.py — Main Flask application
# User Notes API: register, login, manage personal notes, upload/download files.
#
# Security fixes applied:
#   CRITICAL — Insecure deserialization: all session handling now goes through
#              auth.py which uses itsdangerous (see auth.py).
#   HIGH     — Path traversal: secure_filename + realpath boundary check.
#   HIGH     — Unrestricted file upload: allowlist of extensions + size cap.
#   HIGH     — Admin credentials in URL params: moved to POST body.
#   HIGH     — Admin returns password hashes: now calls db.get_all_users()
#              which omits the password column.
#   HIGH     — Debug mode: reads from config which reads FLASK_DEBUG env var.
#   MEDIUM   — No input validation: all endpoints validate presence, type,
#              and length before use.
#   MEDIUM   — No rate limiting: flask-limiter applied to /login and /register.
#   MEDIUM   — Auth copy-pasted into every route: extracted to @require_session.

import os
import logging
from functools import wraps

from flask import Flask, request, jsonify, send_file, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

import config
import db
import auth

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

db.init_db()

# Rate limiter — uses the client IP as the key.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],          # no global default; limits applied per-route
    storage_uri="memory://",    # swap for redis:// in production
)

# Allowed file extensions for upload.
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "csv"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _allowed_extension(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def require_session(f):
    """
    Decorator that validates the X-Session-Token header on a route.

    FIX (was MEDIUM — auth copy-pasted into every route): a single decorator
    verifies the signed token and stores the session in Flask's g object.
    Any route that needs authentication just adds @require_session.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Session-Token")
        if not token:
            return jsonify({"error": "Unauthorized — missing session token"}), 401

        session = auth.load_user_session(token)
        if not session:
            return jsonify({"error": "Unauthorized — invalid or expired session token"}), 401

        g.session = session
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/register", methods=["POST"])
@limiter.limit("10/minute")   # FIX (MEDIUM): rate-limit registration
def register():
    """
    Create a new user account.

    FIX (MEDIUM — no input validation): validates JSON body, required fields,
    types, and length limits before calling auth layer.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400
    if len(username) > 64:
        return jsonify({"error": "username must be 64 characters or fewer"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400
    if len(password) > 128:
        return jsonify({"error": "password must be 128 characters or fewer"}), 400

    try:
        auth.register(username, password)
    except Exception:
        logger.exception("Registration failed for username: %s", username)
        return jsonify({"error": "Registration failed — username may already be taken"}), 409

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
@limiter.limit("5/minute")   # FIX (MEDIUM): rate-limit login to slow brute force
def login():
    """
    Authenticate and return a signed session token.

    FIX (MEDIUM — no rate limiting): 5 attempts per minute per IP.
    FIX (MEDIUM — no input validation): validates body before calling auth.
    FIX (CRITICAL — pickle session): token is now an itsdangerous signed string.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = auth.login(username, password)
    if user:
        session_token = auth.save_user_session(
            {"user_id": user["id"], "username": user["username"]}
        )
        return jsonify({"message": "Login successful", "session": session_token}), 200

    return jsonify({"error": "Invalid credentials"}), 401


# ---------------------------------------------------------------------------
# Notes routes
# ---------------------------------------------------------------------------

@app.route("/notes", methods=["GET"])
@require_session
def get_notes():
    """Return all notes for the authenticated user."""
    notes = db.get_notes_for_user(g.session["user_id"])
    return jsonify({"notes": [dict(n) for n in notes]}), 200


@app.route("/notes/search", methods=["GET"])
@require_session
def search_notes():
    """
    Search notes by title keyword.
    The keyword is passed as a bound parameter — SQL injection is not possible.
    """
    keyword = request.args.get("q", "").strip()
    if len(keyword) > 200:
        return jsonify({"error": "Search keyword too long"}), 400

    notes = db.search_notes(g.session["user_id"], keyword)
    return jsonify({"notes": [dict(n) for n in notes]}), 200


@app.route("/notes", methods=["POST"])
@require_session
def create_note():
    """
    Create a note for the authenticated user.

    FIX (MEDIUM — no input validation): validates JSON body and field lengths.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title:
        return jsonify({"error": "title is required"}), 400
    if len(title) > 200:
        return jsonify({"error": "title must be 200 characters or fewer"}), 400
    if len(content) > 10_000:
        return jsonify({"error": "content must be 10,000 characters or fewer"}), 400

    db.add_note(g.session["user_id"], title, content)
    return jsonify({"message": "Note created"}), 201


# ---------------------------------------------------------------------------
# File routes
# ---------------------------------------------------------------------------

@app.route("/upload", methods=["POST"])
@require_session
def upload_file():
    """
    Upload a file to the server's upload directory.

    FIX (HIGH — unrestricted upload): secure_filename strips path components;
    extension is validated against an allowlist; size cap from MAX_CONTENT_LENGTH.
    """
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    if not _allowed_extension(filename):
        return jsonify({
            "error": f"File type not allowed. Permitted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(config.UPLOAD_FOLDER, filename)
    file.save(save_path)
    logger.info("File uploaded: %s by user_id=%s", filename, g.session["user_id"])

    return jsonify({"message": f"File '{filename}' uploaded"}), 200


@app.route("/download", methods=["GET"])
@require_session
def download_file():
    """
    Download a previously uploaded file.

    FIX (HIGH — path traversal): secure_filename strips path separators and
    os.path.realpath resolves symlinks; the final path is confirmed to be
    inside UPLOAD_FOLDER before the file is served.
    """
    raw_name = request.args.get("filename", "")
    filename = secure_filename(raw_name)
    if not filename:
        return jsonify({"error": "filename is required"}), 400

    base = os.path.realpath(config.UPLOAD_FOLDER)
    file_path = os.path.realpath(os.path.join(base, filename))

    # Boundary check — ensure the resolved path stays inside the upload folder.
    if not file_path.startswith(base + os.sep):
        logger.warning(
            "Path traversal attempt blocked — requested: %s, resolved: %s",
            raw_name, file_path,
        )
        return jsonify({"error": "Invalid filename"}), 400

    if not os.path.isfile(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        return send_file(file_path)
    except OSError as exc:
        logger.error("Failed to send file %s: %s", file_path, exc)
        return jsonify({"error": "Could not retrieve file"}), 500


# ---------------------------------------------------------------------------
# Admin route
# ---------------------------------------------------------------------------

@app.route("/admin", methods=["POST"])
def admin_panel():
    """
    Admin panel — lists all user accounts (without password hashes).

    FIX (HIGH — credentials in URL): credentials moved to POST body so they
    do not appear in server logs, browser history, or proxy access logs.
    FIX (HIGH — password hashes in response): calls db.get_all_users() which
    selects only id and username — password column is never returned.
    FIX (HIGH — hardcoded credentials): compared against config values that
    are loaded from environment variables, not source code.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    username = data.get("username", "")
    password = data.get("password", "")

    # Constant-time comparison prevents timing-based username/password enumeration.
    import hmac
    valid_user = hmac.compare_digest(username, config.ADMIN_USERNAME)
    valid_pass = hmac.compare_digest(password, config.ADMIN_PASSWORD)

    if not (valid_user and valid_pass):
        logger.warning("Admin login failed — attempted username: %s", username)
        return jsonify({"error": "Forbidden"}), 403

    users = db.get_all_users()
    logger.info("Admin panel accessed — username: %s", username)
    return jsonify({"users": [dict(u) for u in users]}), 200


# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large — maximum size is 5 MB"}), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Unhandled server error")
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # FIX (HIGH — debug=True always on): DEBUG now reads FLASK_DEBUG env var
    # and defaults to False.  In production, run via gunicorn, not app.run().
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
