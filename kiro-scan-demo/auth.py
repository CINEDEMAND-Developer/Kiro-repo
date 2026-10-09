# auth.py — Authentication helpers
#
# Security fixes applied:
#   CRITICAL — Insecure deserialization: pickle replaced with itsdangerous
#              URLSafeTimedSerializer (cryptographically signed, 1-hour TTL).
#   HIGH     — Weak hashing: MD5 replaced with bcrypt (salted, work-factor 12).
#   HIGH     — Credential logging: passwords are never written to logs.

import logging
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import config
import db

logger = logging.getLogger(__name__)

# One serializer instance reused across calls.  The secret key comes from the
# environment via config.py — never hardcoded here.
_serializer = URLSafeTimedSerializer(config.SECRET_KEY)

# Token validity window (seconds).  Adjust via environment if needed.
SESSION_MAX_AGE = 3600  # 1 hour


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """
    Return a bcrypt hash of password.

    FIX (was HIGH — MD5, no salt): bcrypt generates a unique random salt
    automatically and embeds it in the returned hash string.  The work factor
    (12 rounds) makes brute-force and rainbow-table attacks computationally
    expensive.
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Constant-time comparison of password against its stored bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def save_user_session(session_obj: dict) -> str:
    """
    Serialize and cryptographically sign a session payload.

    FIX (was CRITICAL — pickle serialization): itsdangerous signs the payload
    with HMAC-SHA1 keyed to SECRET_KEY.  Tampering or forging a token is
    computationally infeasible without the key.  The payload is plain JSON
    (not executable), so there is no deserialization attack surface.
    """
    return _serializer.dumps(session_obj)


def load_user_session(token: str):
    """
    Verify the token signature and return the session payload, or None.

    FIX (was CRITICAL — pickle.loads on untrusted data): only a correctly
    signed, non-expired token produced by save_user_session() will succeed.
    Any tampered, forged, or expired token returns None and is rejected.
    """
    try:
        return _serializer.loads(token, max_age=SESSION_MAX_AGE)
    except SignatureExpired:
        logger.warning("Session token expired")
        return None
    except BadSignature:
        logger.warning("Session token signature invalid — possible tampering")
        return None
    except Exception as exc:
        logger.error("Unexpected error loading session token: %s", exc)
        return None


# ---------------------------------------------------------------------------
# User operations
# ---------------------------------------------------------------------------

def login(username: str, password: str):
    """
    Verify credentials and return the user row, or None on failure.

    FIX (was HIGH — plaintext password in logs): only the username and
    boolean outcome are logged.  The password value is never written anywhere.
    """
    # FIX: log only the username, never the password
    logger.debug("Login attempt — username: %s", username)

    user = db.get_user_by_username(username)
    if user and verify_password(password, user["password"]):
        logger.info("Login success — username: %s", username)
        return user

    logger.warning("Login failed — username: %s", username)
    return None


def register(username: str, password: str) -> None:
    """
    Hash the password with bcrypt and persist the new user.

    FIX (was HIGH — plaintext password in logs): password is not logged at
    any level.  Only the username is recorded after successful registration.
    """
    # FIX: do not log the password
    logger.debug("Registering new user — username: %s", username)
    password_hash = hash_password(password)
    db.add_user(username, password_hash)
    logger.info("User registered — username: %s", username)
