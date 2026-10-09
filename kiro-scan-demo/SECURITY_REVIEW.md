# Security & Code-Quality Review Report

**Project:** kiro-scan-demo  
**Report file:** `SECURITY_REVIEW.md`  
**Review date:** 2026-10-09  
**Reviewer:** AI-assisted static analysis (Kiro CLI)  
**Intended audience:** Technical interviewer, security engineer, DevOps engineer

---

## Executive Summary

### Purpose

This report documents the findings of an AI-assisted static code review and security assessment
of the `kiro-scan-demo` Flask application. The review was conducted to demonstrate how
AI-assisted tooling can accelerate code-quality and security triage during a development
or pre-deployment review cycle.

### Scope

All source files were reviewed by reading them directly and reasoning over their content:

| File | Lines | Role |
|---|---|---|
| `app.py` | 202 | Flask application — all HTTP routes |
| `auth.py` | 61 | Authentication — hashing, session management |
| `db.py` | 92 | SQLite data-access layer |
| `config.py` | 20 | Application configuration and secrets |
| `requirements.txt` | 2 | Direct Python dependencies |
| `README.md` | 32 | Documentation |

### Method

Analysis was performed by static inspection of source code only. No application was started,
no HTTP requests were sent, no payloads were executed, no packages were installed, and no
application files were modified.

### Limitations — Important Disclaimers

> **This is an AI-assisted review, not a certified security audit.**
> It is not a guarantee that all vulnerabilities have been detected, nor a substitute for
> a professional penetration test, a dedicated SAST/DAST scan, or a formal security audit
> conducted by a certified practitioner.

Specific limitations of this review:

- **No runtime execution.** Exploitability of some findings can only be confirmed against
  a running application.
- **No CVE database query.** Dependency vulnerability claims are not made without a
  reliable source. Run `pip-audit` for authoritative results.
- **No fuzzing or dynamic analysis.** Edge cases in request parsing, OS-level path handling,
  and SQLite compile-time options were not tested.
- **Single-pass analysis.** A human reviewer with domain expertise may identify additional
  findings or dismiss some findings as lower-risk in context.

### Finding Counts

| Severity | Security | Code Quality | Total |
|---|---|---|---|
| Critical | 6 | 3 | **9** |
| High | 8 | 6 | **14** |
| Medium | 0 | 6 | **6** |
| Low | 0 | 4 | **4** |
| Unknown | 1 | 0 | **1** |
| **Total** | **15** | **19** | **34** |

> Note: Several code-quality findings (CQ-07, CQ-09, CQ-10, CQ-18, CQ-19) share the same
> root cause as a security finding and are cross-referenced rather than fully duplicated.
> Unique root causes total 28.

### Verification Status Definitions

| Status | Meaning |
|---|---|
| **Confirmed** | The vulnerable or defective code path is unambiguously present and reachable from the documented API surface. Asserted from source evidence alone. |
| **Potential** | The condition exists in source but exploitability depends on a runtime, OS, or deployment factor not determinable statically. |
| **Not Verified** | Could not be confirmed against the actual source code during this review. |

---

## Summary Table

### Security Findings

| ID | Severity | File | Issue | OWASP | Status |
|---|---|---|---|---|---|
| SEC-01 | Critical | `db.py:35–38` | SQL injection — authentication bypass | A03 | Confirmed |
| SEC-02 | Critical | `db.py:46–55` | SQL injection — data extraction via search | A03 | Confirmed |
| SEC-03 | Critical | `auth.py:47–59` | Insecure deserialization (pickle) — RCE via session token | A08 | Confirmed |
| SEC-04 | High | `app.py:148–152` | Path traversal — arbitrary file read | A01 | Confirmed |
| SEC-05 | High | `auth.py:17–18` | Weak password hashing — MD5, no salt | A02 | Confirmed |
| SEC-06 | Critical | `auth.py:47–52` | No session integrity check — token forgery | A07 | Confirmed |
| SEC-07 | Critical | `config.py:8–12` | Hardcoded secrets and credentials | A02/A05 | Confirmed |
| SEC-08 | High | `auth.py:26,37` | Plaintext passwords written to logs | A02 | Confirmed |
| SEC-09 | High | `app.py:160–164` | Admin credentials in URL query parameters | A02 | Confirmed |
| SEC-10 | High | `app.py:166–171` | Admin endpoint returns password hashes | A01 | Confirmed |
| SEC-11 | High | `app.py:119–126` | Unsafe file upload — no type or size validation | A01/A05 | Confirmed |
| SEC-12 | Critical | `config.py:17`, `app.py:198` | Debug mode enabled, bound to `0.0.0.0` | A05 | Confirmed |
| SEC-13 | High | `app.py:39–52` | No brute-force protection on login | A07 | Confirmed |
| SEC-14 | High | `app.py:62–68` | Horizontal privilege escalation via forged `user_id` | A01 | Confirmed |
| SEC-15 | Unknown | `requirements.txt:1–2` | Dependencies not audited against CVE database | A06 | Potential |

### Code-Quality Findings

| ID | Severity | File | Issue | Status |
|---|---|---|---|---|
| CQ-01 | High | `app.py:155` | Wrong HTTP status code (200) on file-not-found error | Confirmed |
| CQ-02 | High | `app.py:31–33,42–44` | `KeyError`/`TypeError` crash on missing or non-JSON body | Confirmed |
| CQ-03 | Medium | `app.py:148` | `None` passed to `os.path.join` when `filename` param is absent | Confirmed |
| CQ-04 | High | `app.py:153–155` | Bare `except:` swallows all exceptions including fatal errors | Confirmed |
| CQ-05 | Medium | `db.py` (all functions) | DB connections not closed on exception — no `with`/`try-finally` | Confirmed |
| CQ-06 | Low | `auth.py:46–51` | Overly broad `except Exception` in `load_user_session` | Confirmed |
| CQ-07 | Critical | `db.py:35–38,46–55` | SQL injection via string concatenation — *see SEC-01, SEC-02* | Confirmed |
| CQ-08 | High | `app.py:31–33` | No input validation on `/register` — duplicates, empty values accepted | Confirmed |
| CQ-09 | High | `app.py:119–121` | No filename sanitisation on upload — *see SEC-11* | Confirmed |
| CQ-10 | High | `app.py:148–150` | Path traversal via unsanitised download param — *see SEC-04* | Confirmed |
| CQ-11 | Medium | `app.py` (5 routes) | Session-check block copy-pasted into five route handlers | Confirmed |
| CQ-12 | Low | `app.py:166–169` | Raw SQL inlined in route handler, bypassing `db.py` | Confirmed |
| CQ-13 | Low | `app.py:17`, `auth.py:8` | `logging.basicConfig` called in two modules | Confirmed |
| CQ-14 | Medium | `db.py` (all functions) | Rows returned as positional tuples — fragile to schema changes | Confirmed |
| CQ-15 | Medium | `auth.py`, `db.py` | No type annotations or docstrings on public functions | Confirmed |
| CQ-16 | Low | `config.py:4` | Relative `DATABASE` path depends on working directory | Confirmed |
| CQ-17 | High | (entire project) | Zero test coverage — no unit, integration, or fixture tests | Confirmed |
| CQ-18 | Critical | `config.py:8–12` | Hardcoded secrets in source — *see SEC-07* | Confirmed |
| CQ-19 | High | `config.py:17` | `DEBUG = True` hardcoded — *see SEC-12* | Confirmed |
| CQ-20 | Medium | `requirements.txt` | Transitive dependencies unpinned; no hash verification | Confirmed |
| CQ-21 | Medium | `config.py:17` | Upload folder set to world-writable `/tmp/uploads` | Potential |

---

## Part 1 — Security Findings

---

### SEC-01 — SQL Injection: Authentication Bypass

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **OWASP** | A03:2021 – Injection |
| **File / Lines** | `db.py`, lines 35–38 |
| **Status** | Confirmed |

**Code evidence**
```python
def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
```

`username` flows from `POST /login` (`app.py` line 43) → `auth.login()` (`auth.py` line 27) →
`db.get_user_by_username()` with no sanitisation at any stage. The value is concatenated
directly into the SQL string.

**Exploit preconditions**  
Unauthenticated network access to `POST /login`. No prior knowledge of valid credentials.

**Proof-of-concept payload (not executed)**
```
username: ' OR '1'='1' --
password: anything
```
Resulting query:
```sql
SELECT * FROM users WHERE username = '' OR '1'='1' --'
```
Returns the first row in the `users` table unconditionally, bypassing authentication entirely.

**Impact**  
Authentication bypass without valid credentials. The attacker is logged in as the first
registered user and inherits their session, notes, and any privileges. If combined with
SEC-06, any `user_id` can be impersonated after a single login.

**Remediation**  
Replace string concatenation with a parameterized query — the correct pattern is already
used in `get_notes_for_user` (db.py line 62):
```python
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

---

### SEC-02 — SQL Injection: Data Extraction via Search

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **OWASP** | A03:2021 – Injection |
| **File / Lines** | `db.py`, lines 46–55 |
| **Status** | Confirmed |

**Code evidence**
```python
def search_notes(user_id, keyword):
    ...
    query = (
        "SELECT * FROM notes WHERE user_id = "
        + str(user_id)
        + " AND title LIKE '%"
        + keyword
        + "%'"
    )
    cursor.execute(query)
```

`keyword` originates from `request.args.get("q", "")` in `app.py` line 84 — a raw HTTP
query parameter. No sanitisation is applied at the route or before the database call.

**Exploit preconditions**  
Valid session token (obtainable via registration, or bypassed via SEC-01 or SEC-06).
HTTP GET access to `/notes/search`.

**Proof-of-concept payload (not executed)**
```
GET /notes/search?q=%' UNION SELECT id,username,password,4 FROM users --
```
Appends a `UNION SELECT` to the query, returning all usernames and password hashes from
the `users` table embedded in the notes response.

**Impact**  
Cross-user data exfiltration. Dump of the entire `users` table including MD5 password
hashes (crackable offline — see SEC-05). Schema enumeration via `sqlite_master`. Combined
with SEC-06, `user_id` in the query can be bypassed too.

**Remediation**
```python
cursor.execute(
    "SELECT * FROM notes WHERE user_id = ? AND title LIKE ?",
    (user_id, f"%{keyword}%")
)
```

---

### SEC-03 — Insecure Deserialization: RCE via Session Token

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **OWASP** | A08:2021 – Software and Data Integrity Failures |
| **File / Lines** | `auth.py`, lines 47–59 |
| **Status** | Confirmed |

**Code evidence**
```python
# Token generation — server sends this to the client at login
def save_user_session(session_obj: dict) -> str:
    raw = pickle.dumps(session_obj)
    return base64.b64encode(raw).decode()

# Token verification — called on every authenticated request
def load_user_session(session_data: str):
    try:
        raw = base64.b64decode(session_data)
        session = pickle.loads(raw)   # DANGER: never unpickle untrusted data
        return session
    except Exception as e:
        ...
```

The session token is a base64-encoded pickle payload. It is issued at login (`app.py` line 50),
sent to the client in the JSON response, and accepted back on every request via the
`X-Session-Token` header. The server applies no HMAC, no digital signature, and no
server-side session store lookup before calling `pickle.loads()`.

**Exploit preconditions**  
Network access to any authenticated endpoint. No prior account is required — the attacker
constructs a valid pickle payload from scratch without needing to register or log in.

**Proof-of-concept (Python pseudocode, not executed)**
```python
import pickle, base64, os

class Exploit(object):
    def __reduce__(self):
        return (os.system, ("id > /tmp/pwned",))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
# Send as X-Session-Token to: GET /notes, POST /notes,
# GET /notes/search, POST /upload, GET /download
```
When `pickle.loads()` deserializes this payload, `os.system("id > /tmp/pwned")` executes
as the web server's OS user before the route handler runs.

**Impact**  
Unauthenticated remote code execution on the server. Complete system compromise: read
any file, write files, install persistent backdoors, exfiltrate the database, pivot to
internal networks. This is the highest-impact finding in the codebase.

**Remediation**  
Replace pickle entirely. Use `itsdangerous.URLSafeTimedSerializer`, which is already a
transitive dependency of Flask and requires no new packages:
```python
from itsdangerous import URLSafeTimedSerializer

s = URLSafeTimedSerializer(config.SECRET_KEY)

def save_user_session(session_obj: dict) -> str:
    return s.dumps(session_obj)

def load_user_session(session_data: str):
    try:
        return s.loads(session_data, max_age=3600)
    except Exception:
        return None
```
This also resolves SEC-06 (token forgery) simultaneously.

---

### SEC-04 — Path Traversal: Arbitrary File Read

| Field | Detail |
|---|---|
| **Severity** | High |
| **OWASP** | A01:2021 – Broken Access Control |
| **File / Lines** | `app.py`, lines 148–152 |
| **Status** | Confirmed |

**Code evidence**
```python
filename  = request.args.get("filename")
file_path = os.path.join(config.UPLOAD_FOLDER, filename)
...
return send_file(file_path)
```

`UPLOAD_FOLDER` is `/tmp/uploads` (`config.py` line 17). Python's `os.path.join` does not
constrain the result to the base directory when the second argument contains `../` sequences.

**Exploit preconditions**  
Valid session token. HTTP GET access to `/download`.

**Proof-of-concept (not executed)**
```
GET /download?filename=../../etc/passwd
```
`os.path.join("/tmp/uploads", "../../etc/passwd")` resolves to `/etc/passwd`.
`send_file` reads and transmits the file to the caller.

**Impact**  
Read any file accessible to the server process: `/etc/shadow`, SSH private keys,
the `users.db` SQLite file (if its absolute path is known), application source code,
`.env` files, or cloud instance metadata endpoints on some platforms.

**Remediation**
```python
from werkzeug.utils import secure_filename

safe_base  = os.path.abspath(config.UPLOAD_FOLDER)
safe_name  = secure_filename(filename)
if not safe_name:
    return jsonify({"error": "Invalid filename"}), 400
requested  = os.path.abspath(os.path.join(safe_base, safe_name))
if not requested.startswith(safe_base + os.sep):
    return jsonify({"error": "Invalid filename"}), 400
return send_file(requested)
```

*Also see: CQ-10 (same root cause from a code-quality perspective).*

---

### SEC-05 — Weak Password Hashing: MD5 Without Salt

| Field | Detail |
|---|---|
| **Severity** | High |
| **OWASP** | A02:2021 – Cryptographic Failures |
| **File / Lines** | `auth.py`, lines 17–18 |
| **Status** | Confirmed |

**Code evidence**
```python
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
```

MD5 is a general-purpose digest algorithm, not a password hashing function. It has
no work factor and no salt. The result is stored as the `password` column in the
`users` table and returned by the `/admin` endpoint (see SEC-10).

**Why MD5 is unsuitable for passwords:**
- A modern GPU computes ~60 billion MD5 hashes/second. An 8-character lowercase
  password space (~200 billion combinations) is exhausted in under 4 seconds.
- Without a salt, identical passwords produce identical hashes. A single rainbow table
  attack cracks all affected users simultaneously.
- The hash `5f4dcc3b5aa765d61d8327deb882cf99` is immediately recognized as `password`
  by public lookup databases (e.g., CrackStation) without computation.

**Impact**  
Offline cracking of all user passwords within minutes to hours of any hash leak.
Credential reuse attacks against email, banking, and other services if users share passwords.

**Remediation**
```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```
Alternatives: `argon2-cffi` (Argon2id — current Password Hashing Competition winner)
or `passlib` with a bcrypt backend.

---

### SEC-06 — No Session Integrity Verification: Token Forgery

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **OWASP** | A07:2021 – Identification and Authentication Failures |
| **File / Lines** | `auth.py`, lines 47–52; `app.py`, lines 62–65, 78–81, 91–94, 125–128, 139–142 |
| **Status** | Confirmed |

**Code evidence**
```python
# The sole "verification" step on every authenticated request
raw     = base64.b64decode(session_data)
session = pickle.loads(raw)
return session
```

Base64 is an encoding, not a cryptographic signature. Any value that base64-decodes to a
valid pickle object is accepted as a legitimate session. The server does not verify that
the token was issued by itself.

**Independent attack (separate from SEC-03):**  
A legitimate user receives `{"user_id": 3, "username": "attacker"}` at login. They
re-serialize `{"user_id": 1, "username": "admin"}` with pickle and base64-encode it.
The server accepts it — no injection, no exploit, just encoding.

**Impact**  
Session forgery and impersonation of any user. Horizontal privilege escalation (access any
user's notes by enumerating sequential integer IDs). Vertical escalation to user ID 1
(typically the first registered or admin account). Compounds every other authenticated
vulnerability.

**Remediation**  
Fully resolved by adopting `itsdangerous.URLSafeTimedSerializer` as described in SEC-03.
No separate fix is needed beyond replacing the pickle scheme.

---

### SEC-07 — Hardcoded Secrets and Credentials

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **OWASP** | A02:2021 – Cryptographic Failures / A05:2021 – Security Misconfiguration |
| **File / Lines** | `config.py`, lines 8–12 |
| **Status** | Confirmed |

**Code evidence**
```python
SECRET_KEY     = "supersecret123"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
```

Three secrets are committed directly to source code. Git history preserves them permanently
even after the lines are deleted. `SECRET_KEY` is loaded into `app.secret_key`
(`app.py` line 14) and used for Flask cookie signing. Admin credentials are compared
directly in `admin_panel()` (`app.py` lines 162–164).

**Impact**  
Anyone with repository access (CI runner, contractor, public GitHub viewer) can:
- Access the admin panel immediately using `admin`/`admin123`.
- Forge Flask session cookies if a HMAC-based token scheme replaces pickle.
- Enumerate the secret key in any dependent security control.
- Credentials cannot be rotated without a code deploy.

**Remediation**
```python
import os

SECRET_KEY     = os.environ["SECRET_KEY"]      # KeyError at startup if absent
ADMIN_USERNAME = os.environ["ADMIN_USERNAME"]  # KeyError at startup if absent — no default
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]  # KeyError at startup if absent
```
All three values must be set explicitly in the environment before the application starts.
Defaulting `ADMIN_USERNAME` to `"admin"` would preserve a known-weak credential in any
deployment that omits the variable, so no default is provided. If a default is required
for a specific environment, it must be set explicitly in that environment's configuration
(e.g., a `.env` file that is never committed to version control), not in source code.

Rotate all three values immediately. Scan git history to find all commits that contained
the original hardcoded values:
```bash
git log -S "supersecret123" --all
git log -S "admin123" --all
```

*Also see: CQ-18 (same root cause from a code-quality perspective).*

---

### SEC-08 — Plaintext Passwords Written to Application Logs

| Field | Detail |
|---|---|
| **Severity** | High |
| **OWASP** | A02:2021 – Cryptographic Failures |
| **File / Lines** | `auth.py`, lines 26, 37 |
| **Status** | Confirmed |

**Code evidence**
```python
def login(username, password):
    logger.debug("Login attempt — username: %s  password: %s", username, password)

def register(username, password):
    logger.debug("Registering new user — username: %s  password: %s", username, password)
```

Raw plaintext passwords are emitted at `DEBUG` level on every login and registration attempt.
`logging.basicConfig(level=logging.DEBUG)` is set in both `auth.py` (line 8) and `app.py`
(line 16), so these log lines always execute.

**Impact**  
Credentials harvested from: log files on disk, log aggregation platforms (Datadog, Splunk,
CloudWatch), container stdout captures, systemd journals, or any observer of the logging
pipeline. Log platforms typically grant broader access than the application server itself
and retain data for 30–90+ days.

**Remediation**  
Remove the `password` argument from all log statements entirely:
```python
logger.debug("Login attempt — username: %s", username)
logger.info("Login success — username: %s", username)
logger.warning("Login failed — username: %s", username)
```

---

### SEC-09 — Admin Credentials in URL Query Parameters

| Field | Detail |
|---|---|
| **Severity** | High |
| **OWASP** | A02:2021 – Cryptographic Failures |
| **File / Lines** | `app.py`, lines 160–164 |
| **Status** | Confirmed |

**Code evidence**
```python
@app.route("/admin", methods=["GET"])
def admin_panel():
    username = request.args.get("username")
    password = request.args.get("password")
    if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
```

Authentication is performed by passing credentials as URL query parameters:
`GET /admin?username=admin&password=admin123`.

**Where these credentials appear in plaintext:**
- Server access logs (Apache/Nginx combined log format logs the full URL by default)
- Flask/Werkzeug debug output
- Browser history and bookmarks
- HTTP `Referer` header if the page links outward
- Shared proxy and load balancer logs
- Network captures (on plaintext HTTP)

**Impact**  
Admin credentials exposed to every log viewer, proxy administrator, or network observer
in the path. Grants access to the full user list including password hashes (SEC-10).

**Remediation**  
Move credentials to the `Authorization` header transmitted over HTTPS, or implement a
POST-based login form with CSRF protection. Never place secrets in query strings.

---

### SEC-10 — Admin Endpoint Returns Password Hashes

| Field | Detail |
|---|---|
| **Severity** | High |
| **OWASP** | A01:2021 – Broken Access Control |
| **File / Lines** | `app.py`, lines 166–171 |
| **Status** | Confirmed |

**Code evidence**
```python
cursor.execute("SELECT id, username, password FROM users")
users = cursor.fetchall()
conn.close()
return jsonify({"users": users}), 200
```

The `password` column (MD5 hashes) is explicitly selected and returned in the API response
body. Even in a legitimate admin use case, returning credential material over an API is
unnecessary and dangerous.

**Impact**  
Combined with SEC-05 (MD5, no salt), the returned hashes are immediately crackable offline,
yielding plaintext passwords for all users. The attacker needs only to know `admin`/`admin123`
(hardcoded — SEC-07) to trigger this endpoint.

**Remediation**  
Exclude the password column from the query:
```python
cursor.execute("SELECT id, username FROM users")
```

---

### SEC-11 — Unsafe File Upload: No Type or Size Validation

| Field | Detail |
|---|---|
| **Severity** | High |
| **OWASP** | A01:2021 – Broken Access Control / A05:2021 – Security Misconfiguration |
| **File / Lines** | `app.py`, lines 119–126 |
| **Status** | Confirmed |

**Code evidence**
```python
filename  = file.filename
save_path = os.path.join(config.UPLOAD_FOLDER, filename)
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
file.save(save_path)
```

`file.filename` is attacker-controlled. No extension allowlist, MIME-type check,
`secure_filename` call, content inspection, or file size limit is applied.

**Specific attack vectors:**
1. Upload `shell.py` or `exploit.sh` to `/tmp/uploads/`. If any server process executes
   scripts from that directory, it runs attacker code.
2. Upload a file named `../app.py` — `os.path.join` may resolve outside the upload folder
   depending on OS path handling (runtime-dependent — see Unverified Claims).
3. Upload a 4 GB file with no `MAX_CONTENT_LENGTH` set — denial of service via disk
   or memory exhaustion.
4. Upload `.htaccess` or `web.config` if the directory is ever served statically.

**Impact**  
Potential server-side code execution, write-side path traversal, denial of service.

**Remediation**
```python
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

filename = secure_filename(file.filename)
if not filename or not allowed_file(filename):
    return jsonify({"error": "File type not allowed"}), 400
```
Add to `app.py` startup: `app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB`

*Also see: CQ-09 (same root cause from a code-quality perspective).*

---

### SEC-12 — Debug Mode Enabled, Bound to All Network Interfaces

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **OWASP** | A05:2021 – Security Misconfiguration |
| **File / Lines** | `config.py`, line 17; `app.py`, line 198 |
| **Status** | Confirmed |

**Code evidence**
```python
# config.py
DEBUG = True

# app.py
app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
```

`debug=True` activates Werkzeug's interactive debugger. When any unhandled exception occurs,
the browser renders a full traceback with an interactive Python REPL on each stack frame.
`host="0.0.0.0"` exposes this on all network interfaces.

The debugger is protected by a PIN, but that PIN is derived deterministically from:
the OS username, the absolute path of the Flask file, the machine ID (`/etc/machine-id`),
and the MAC address of the first network interface. On many cloud VMs and containers,
these values are discoverable through other means (e.g., path traversal via SEC-04).
This is a publicly documented attack chain against Flask applications left in debug mode.

**Triggering the exception** is trivial: send `POST /register` with no body or with a
non-JSON `Content-Type`. The `data["username"]` access raises `TypeError` on `None`,
producing an unhandled exception that opens the debugger.

**Impact**  
Interactive Python shell on the server accessible over the network. Equivalent to a
direct OS shell. Full system compromise without authentication.

**Remediation**
```python
# config.py
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
```
In development environments, bind to `127.0.0.1` only:
```python
app.run(debug=config.DEBUG, host="127.0.0.1", port=5000)
```

*Also see: CQ-19 (same root cause from a code-quality perspective).*

---

### SEC-13 — No Brute-Force Protection on Login

| Field | Detail |
|---|---|
| **Severity** | High |
| **OWASP** | A07:2021 – Identification and Authentication Failures |
| **File / Lines** | `app.py`, lines 39–52 |
| **Status** | Confirmed |

**Code evidence**
```python
@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = data["username"]
    password = data["password"]
    user     = auth.login(username, password)
    if user:
        ...
    return jsonify({"error": "Invalid credentials"}), 401
```

No IP-based rate limiting, no per-account lockout counter, no progressive delay, and no
CAPTCHA are implemented anywhere in the application.

**Impact**  
Unlimited password guessing at network speed. At 1,000 requests/second (easily achievable
with a tool like `hydra` or a simple `asyncio` script), the 10,000 most common passwords
are exhausted in 10 seconds per username. Combined with SEC-05 (MD5, no salt), offline
cracking of any leaked hash is faster still.

**Remediation**  
Apply `Flask-Limiter` at the route level:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    ...
```
Implement account lockout after N consecutive failures (e.g., 10) with a timed unlock.

---

### SEC-14 — Horizontal Privilege Escalation via Forged `user_id`

| Field | Detail |
|---|---|
| **Severity** | High |
| **OWASP** | A01:2021 – Broken Access Control |
| **File / Lines** | `app.py`, lines 62–68 |
| **Status** | Confirmed |

**Code evidence**
```python
session  = auth.load_user_session(session_data)
...
user_id  = session["user_id"]
notes    = db.get_notes_for_user(user_id)
```

`user_id` is sourced from the unsigned session token (SEC-06). The database query in
`get_notes_for_user` correctly filters by `user_id`, but the `user_id` value itself is
entirely attacker-controlled. User IDs are sequential integers starting at 1
(AUTOINCREMENT in `db.py` line 13), making enumeration trivial.

**Impact**  
Any authenticated user reads or creates notes belonging to any other user. Complete
data confidentiality failure between users.

**Remediation**  
Fully resolved by fixing SEC-06 (signed session tokens). Once `user_id` in the token
cannot be tampered with, the data query is safe. No separate code change required.

---

### SEC-15 — Dependency Versions Not Audited Against CVE Database

| Field | Detail |
|---|---|
| **Severity** | Unknown |
| **OWASP** | A06:2021 – Vulnerable and Outdated Components |
| **File / Lines** | `requirements.txt`, lines 1–2 |
| **Status** | Potential |

**Code evidence**
```
Flask==2.3.3
Werkzeug==2.3.7
```

Direct dependencies are pinned (good practice). Flask 2.3.x and Werkzeug 2.3.x are older
releases; Flask 3.x is the current major release as of 2024. Transitive dependencies
(`Jinja2`, `MarkupSafe`, `click`, `itsdangerous`) are not pinned and no hash verification
is used.

**What cannot be confirmed in this review:**  
No CVE database, `pip-audit`, `safety`, or Snyk scan was run. No specific CVE is asserted
for these versions. Doing so without a reliable source would be speculation.

**Remediation**  
Run `pip-audit` in CI to continuously check pinned versions against the PyPA advisory
database:
```bash
pip install pip-audit
pip-audit -r requirements.txt
```
Use `pip-compile --generate-hashes` (from `pip-tools`) to lock and hash all transitive
dependencies.

---

## Part 2 — Code-Quality Findings

---

### CQ-01 — Wrong HTTP Status Code on Download Failure

| Field | Detail |
|---|---|
| **Severity** | High |
| **File / Lines** | `app.py`, line 155 |
| **Status** | Confirmed |

**Code evidence**
```python
    except:
        return jsonify({"error": "File not found"}), 200   # wrong status code too
```

HTTP 200 OK is returned when a file is not found or when any other exception occurs.
HTTP 200 tells every client, monitoring tool, and load balancer that the request succeeded.

**Impact**  
Client-side error handling breaks. Alerting and SLO dashboards miss failures. Automated
tests that check status codes cannot detect this failure mode.

**Remediation**  
Return `404` for `FileNotFoundError`, `400` for a missing `filename` parameter,
`500` (or raise and let Flask's error handler fire) for anything else.

---

### CQ-02 — `KeyError`/`TypeError` Crash on Missing or Non-JSON Request Body

| Field | Detail |
|---|---|
| **Severity** | High |
| **File / Lines** | `app.py`, lines 31–33, 42–44, 97–98 |
| **Status** | Confirmed |

**Code evidence**
```python
data     = request.get_json()   # returns None if Content-Type is not application/json
username = data["username"]     # TypeError on None; KeyError if key is absent
password = data["password"]
```

The same unguarded pattern appears in `/register` (lines 31–33), `/login` (lines 42–44),
and `/notes` POST (lines 97–98). Flask's default handler for an unhandled `TypeError`
returns an HTML 500, breaking JSON API clients and — when `DEBUG = True` — triggering the
Werkzeug interactive debugger (SEC-12).

**Impact**  
API clients crash. Debug mode exposes the full traceback to the caller. The unhandled
exception path also bypasses the bare-except in the download route, so different routes
have inconsistent error behavior.

**Remediation**
```python
data     = request.get_json(silent=True) or {}
username = data.get("username", "").strip()
password = data.get("password", "")
if not username or not password:
    return jsonify({"error": "username and password are required"}), 400
```

---

### CQ-03 — `None` Passed to `os.path.join` When `filename` Parameter Is Absent

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File / Lines** | `app.py`, line 148 |
| **Status** | Confirmed |

**Code evidence**
```python
filename  = request.args.get("filename")          # returns None if param is absent
file_path = os.path.join(config.UPLOAD_FOLDER, filename)   # TypeError: expected str
```

The `TypeError` is raised before the `try/except` block even runs (line 153), so the
bare-except at line 154 does not catch it. Flask's unhandled-exception handler fires,
returning an HTML 500 or opening the debugger.

**Remediation**
```python
filename = request.args.get("filename", "").strip()
if not filename:
    return jsonify({"error": "filename parameter is required"}), 400
```

---

### CQ-04 — Bare `except:` Swallows All Exceptions Including Fatal Errors

| Field | Detail |
|---|---|
| **Severity** | High |
| **File / Lines** | `app.py`, lines 153–155 |
| **Status** | Confirmed |

**Code evidence**
```python
    try:
        return send_file(file_path)
    except:
        return jsonify({"error": "File not found"}), 200
```

A bare `except:` (no exception type) catches everything, including `SystemExit`,
`KeyboardInterrupt`, `MemoryError`, and programmer errors (`AttributeError`, `NameError`).
No exception information is logged. The misleading error message and wrong status code
(200) compound the problem (CQ-01).

**Remediation**
```python
    try:
        return send_file(file_path)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except PermissionError:
        return jsonify({"error": "Access denied"}), 403
    except Exception:
        logger.exception("Unexpected error serving file: %s", file_path)
        return jsonify({"error": "Internal server error"}), 500
```

---

### CQ-05 — Database Connections Not Closed on Exception

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File / Lines** | `db.py` — all five functions |
| **Status** | Confirmed |

**Code evidence**
```python
def get_user_by_username(username):
    conn   = get_connection()
    cursor = conn.cursor()
    ...
    cursor.execute(query)   # if this raises, conn.close() below is never reached
    user = cursor.fetchone()
    conn.close()
    return user
```

The same pattern appears in `search_notes`, `get_notes_for_user`, `add_note`, and
`add_user`. A `sqlite3.OperationalError` or `sqlite3.DatabaseError` during execution
leaks the connection. Under concurrent load this causes SQLite lock starvation.

**Remediation**  
`sqlite3`'s `with conn:` context manager handles **transaction commit/rollback only** — it
does not close the underlying connection. For a long-running web server, the connection
must be closed explicitly to release the file handle. Use one of the following patterns:

**Option A — `try/finally` (explicit, recommended for clarity):**
```python
def get_user_by_username(username: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()   # always runs, whether or not an exception occurred
```

**Option B — `contextlib.closing` (closes on exit) combined with `with conn:` (transaction):**
```python
from contextlib import closing

def get_user_by_username(username: str):
    with closing(sqlite3.connect(config.DATABASE)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:   # inner `with conn:` handles commit/rollback
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            return cursor.fetchone()
```
`contextlib.closing` guarantees `conn.close()` is called when the outer `with` block exits,
while the inner `with conn:` block handles commit on success and rollback on exception.

Apply the same pattern to `search_notes`, `get_notes_for_user`, `add_note`, and `add_user`.

---

### CQ-06 — Overly Broad `except Exception` in Session Loader

| Field | Detail |
|---|---|
| **Severity** | Low |
| **File / Lines** | `auth.py`, lines 46–51 |
| **Status** | Confirmed |

**Code evidence**
```python
    except Exception as e:
        logger.error("Failed to load session: %s", e)
        return None
```

`MemoryError` and other fatal conditions would silently return `None`, producing a 401
response with no indication that a server error occurred.

**Remediation**  
Catch only the expected failure modes for malformed input:
```python
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning("Malformed session token: %s", e)
        return None
```

---

### CQ-07 — SQL Injection via String Concatenation (Root Cause of SEC-01, SEC-02)

*See SEC-01 and SEC-02 for full details, code evidence, exploit preconditions, impact,
and remediation. This entry documents the same issue from a code-quality perspective:
the root cause is the inconsistent application of parameterized queries. The correct
pattern already exists in the same file (`get_notes_for_user`, `add_note`, `add_user`)
and simply needs to be applied to the remaining two functions.*

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **File / Lines** | `db.py`, lines 35–38, 46–55 |
| **Status** | Confirmed |

---

### CQ-08 — No Input Validation on `/register`

| Field | Detail |
|---|---|
| **Severity** | High |
| **File / Lines** | `app.py`, lines 31–33 |
| **Status** | Confirmed |

**Code evidence**
```python
username = data["username"]
password = data["password"]
auth.register(username, password)
```

No length, type, character, or uniqueness check. The `users` table (`db.py` lines 12–18)
has no `UNIQUE` constraint on `username`, so duplicate registrations are silently accepted.
Because `get_user_by_username` returns the first match, a second registration of the same
username does not grant access to the first user's data, but creates an orphaned account
and causes confusion.

**Remediation**  
Validate inputs before use:
```python
if not isinstance(username, str) or not (3 <= len(username) <= 64):
    return jsonify({"error": "username must be 3–64 characters"}), 400
if not isinstance(password, str) or len(password) < 8:
    return jsonify({"error": "password must be at least 8 characters"}), 400
```
Add `UNIQUE` constraint to schema: `username TEXT NOT NULL UNIQUE`.

---

### CQ-09 — No Filename Sanitisation on Upload (Root Cause of SEC-11)

*See SEC-11 for full details, code evidence, impact, and remediation. From a code-quality
perspective the root cause is the absence of `werkzeug.utils.secure_filename` and an
extension allowlist — both of which are straightforward, low-effort additions.*

| Field | Detail |
|---|---|
| **Severity** | High |
| **File / Lines** | `app.py`, lines 119–121 |
| **Status** | Confirmed |

---

### CQ-10 — Path Traversal via Unsanitised Download Parameter (Root Cause of SEC-04)

*See SEC-04 for full details, code evidence, impact, and remediation. From a code-quality
perspective the root cause is the absence of an absolute-path boundary check after
`os.path.join`.*

| Field | Detail |
|---|---|
| **Severity** | High |
| **File / Lines** | `app.py`, lines 148–150 |
| **Status** | Confirmed |

---

### CQ-11 — Session-Check Block Copy-Pasted Into Five Route Handlers

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File / Lines** | `app.py`, lines 58–65, 75–82, 88–95, 123–130, 137–144 |
| **Status** | Confirmed |

**Code evidence** (identical block repeated five times)
```python
session_data = request.headers.get("X-Session-Token")
if not session_data:
    return jsonify({"error": "Unauthorized"}), 401
session = auth.load_user_session(session_data)
if not session:
    return jsonify({"error": "Invalid session"}), 401
```

Any future change to the session mechanism (e.g., switching from pickle to JWT) requires
editing five places, with the risk of missing one and introducing an inconsistency.

**Remediation**  
Extract into a decorator:
```python
from functools import wraps

def require_session(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Session-Token")
        if not token:
            return jsonify({"error": "Unauthorized"}), 401
        session = auth.load_user_session(token)
        if not session:
            return jsonify({"error": "Invalid session"}), 401
        request.session = session
        return f(*args, **kwargs)
    return wrapper

# Usage
@app.route("/notes", methods=["GET"])
@require_session
def get_notes():
    user_id = request.session["user_id"]
    ...
```

---

### CQ-12 — Raw SQL Inlined in Route Handler, Bypassing `db.py`

| Field | Detail |
|---|---|
| **Severity** | Low |
| **File / Lines** | `app.py`, lines 166–169 |
| **Status** | Confirmed |

**Code evidence**
```python
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, username, password FROM users")
users = cursor.fetchall()
conn.close()
```

`app.py` bypasses the data-access layer entirely and executes raw SQL directly. The
`password` column selection (a security issue in its own right — SEC-10) is buried in
route code rather than in a function that could be audited and controlled centrally.

**Remediation**  
Add `get_all_users()` to `db.py` (returning only `id` and `username`), call it from
`admin_panel`, and remove the inline SQL from `app.py`.

---

### CQ-13 — `logging.basicConfig` Called in Two Modules

| Field | Detail |
|---|---|
| **Severity** | Low |
| **File / Lines** | `app.py`, line 17; `auth.py`, line 8 |
| **Status** | Confirmed |

**Code evidence**
```python
# app.py line 17
logging.basicConfig(level=logging.DEBUG)

# auth.py line 8
logging.basicConfig(level=logging.DEBUG)
```

Python's `logging.basicConfig` is idempotent after the first call — the second call is a
no-op. This creates the false impression that `auth.py` independently configures its logging
level. A developer who changes the level in one file will be confused when the other
module does not appear to follow.

**Remediation**  
Call `logging.basicConfig` exactly once in `app.py` at startup. Remove the call from
`auth.py`. Each module should only call `logging.getLogger(__name__)`.

---

### CQ-14 — Rows Returned as Positional Tuples

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File / Lines** | `db.py` (all functions); `app.py`, line 49 |
| **Status** | Confirmed |

**Code evidence**
```python
# app.py line 49
session_token = auth.save_user_session({"user_id": user[0], "username": user[1]})
```

Callers access column values by integer index (`user[0]`, `user[1]`, `user[2]`). If any
column is added, removed, or reordered in the `CREATE TABLE` statement, every positional
access silently reads the wrong value with no error at runtime.

**Remediation**  
Set `conn.row_factory = sqlite3.Row` in `get_connection()`:
```python
def get_connection():
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
```
This gives named access everywhere: `user["id"]`, `user["username"]`, `user["password"]`.

---

### CQ-15 — No Type Annotations or Docstrings on Public Functions

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File / Lines** | `auth.py`, `db.py` (all public functions) |
| **Status** | Confirmed |

**Code evidence**
```python
def get_user_by_username(username):   # return type unknown — tuple or None?
def login(username, password):         # return type unknown — tuple or None?
def search_notes(user_id, keyword):   # what type is user_id? int or str?
```

Callers must read the full implementation to determine return types, nullability, and
exception behavior. This is especially important for `login()` and `get_user_by_username()`
where a `None` return drives authentication logic.

**Remediation**  
Add PEP 484 type annotations and short docstrings:
```python
from typing import Optional

def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    """Return the user row for `username`, or None if not found."""
```

---

### CQ-16 — Relative `DATABASE` Path Depends on Launch Working Directory

| Field | Detail |
|---|---|
| **Severity** | Low |
| **File / Lines** | `config.py`, line 4 |
| **Status** | Confirmed |

**Code evidence**
```python
DATABASE = "users.db"
```

This resolves relative to whichever directory `python app.py` is run from. Running from
`~/` versus `~/Desktop/kiro-scan-demo/` silently creates two separate database files,
causing confusing "user not found" errors that are difficult to trace.

**Remediation**
```python
import os
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
```

---

### CQ-17 — Zero Test Coverage

| Field | Detail |
|---|---|
| **Severity** | High |
| **File / Lines** | Entire project — no `tests/` directory or `test_*.py` files exist |
| **Status** | Confirmed |

No unit tests, integration tests, or fixture data exist anywhere in the workspace.
Specific untested behaviors:

- `hash_password` / `verify_password` — correct MD5 output and round-trip
- `get_user_by_username` — SQL injection susceptibility
- `load_user_session` / `save_user_session` — pickle round-trip, malformed input, `None` return
- All five routes — happy path, missing fields, bad session, wrong HTTP methods
- `/admin` — forbidden response for wrong credentials

**Remediation**  
Add a `tests/` directory. Use `pytest` with Flask's built-in test client.
Use `DATABASE = ":memory:"` for test isolation:
```python
# tests/conftest.py
import pytest
from app import app
import config

@pytest.fixture
def client():
    config.DATABASE = ":memory:"
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
```

---

### CQ-18 — Hardcoded Secrets (Root Cause of SEC-07)

*See SEC-07 for full details, code evidence, impact, and remediation. From a code-quality
perspective the root cause is the absence of environment-variable-based configuration and
a fail-safe startup check.*

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **File / Lines** | `config.py`, lines 8–12 |
| **Status** | Confirmed |

---

### CQ-19 — `DEBUG = True` Hardcoded (Root Cause of SEC-12)

*See SEC-12 for full details, code evidence, impact, and remediation. From a code-quality
perspective the root cause is the absence of an environment-aware configuration switch.*

| Field | Detail |
|---|---|
| **Severity** | High |
| **File / Lines** | `config.py`, line 16 |
| **Status** | Confirmed |

---

### CQ-20 — Transitive Dependencies Unpinned, No Hash Verification

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File / Lines** | `requirements.txt`, lines 1–2 |
| **Status** | Confirmed |

**Code evidence**
```
Flask==2.3.3
Werkzeug==2.3.7
```

Only two direct dependencies are pinned. Transitive packages (`Jinja2`, `MarkupSafe`,
`click`, `itsdangerous`) resolve to whatever versions are current at install time.
No `--require-hashes` is used, leaving the install open to dependency confusion or
a compromised PyPI mirror.

**Remediation**  
Generate a fully locked, hash-verified requirements file:
```bash
pip install pip-tools
pip-compile --generate-hashes requirements.in > requirements.txt
```

---

### CQ-21 — Upload Folder Set to World-Writable `/tmp/uploads`

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **File / Lines** | `config.py`, line 17 |
| **Status** | Potential |

**Code evidence**
```python
UPLOAD_FOLDER = "/tmp/uploads"
```

`/tmp` is world-writable on standard Linux and macOS. Any local process or user on the
same host can read, overwrite, or delete uploaded files. On some systems `/tmp` is a
`tmpfs` mount cleared on reboot, causing silent data loss. On shared hosting, this may
expose files to other tenants.

*Exploitability is environment-dependent — confirmed in source; runtime behavior varies
by OS and mount configuration.*

**Remediation**  
Store uploads in an application-owned directory outside `/tmp`, configured via environment
variable:
```python
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/var/data/kiro-scan-demo/uploads")
```

---

## Prioritized Remediation Plan

Fixes are grouped by effort level. All "Immediate" items are low-effort but eliminate
the highest-impact vulnerabilities.

### Immediate — Eliminate Critical/RCE-class Issues

| Step | Finding(s) | Action | Effort |
|---|---|---|---|
| 1 | SEC-03, SEC-06 | Replace `pickle` with `itsdangerous.URLSafeTimedSerializer` | ~15 min |
| 2 | SEC-07, CQ-18 | Move `SECRET_KEY`, `ADMIN_PASSWORD` to `os.environ` | ~10 min |
| 3 | SEC-12, CQ-19 | Make `DEBUG` environment-controlled; bind dev to `127.0.0.1` | ~5 min |

### High Priority — Fix Injection and Access Control

| Step | Finding(s) | Action | Effort |
|---|---|---|---|
| 4 | SEC-01, SEC-02, CQ-07 | Parameterize all SQL queries in `db.py` | ~20 min |
| 5 | SEC-04, CQ-10 | Add path boundary check in `download_file` | ~10 min |
| 6 | SEC-05 | Replace MD5 with `bcrypt` in `auth.py` | ~15 min |
| 7 | SEC-08 | Remove passwords from all `logger.debug` calls | ~5 min |
| 8 | SEC-11, CQ-09 | Add `secure_filename` + extension allowlist in `upload_file` | ~15 min |
| 9 | SEC-13 | Add `Flask-Limiter` rate limit on `/login` | ~15 min |
| 10 | SEC-10 | Remove `password` from `SELECT` in `/admin` | ~2 min |
| 11 | SEC-09 | Move admin auth to `Authorization` header | ~30 min |

### Medium Priority — Improve Robustness

| Step | Finding(s) | Action | Effort |
|---|---|---|---|
| 12 | CQ-02, CQ-08 | Add input validation on all request bodies | ~30 min |
| 13 | CQ-01, CQ-04 | Fix status codes; replace bare `except:` with typed catches | ~20 min |
| 14 | CQ-11 | Extract session check into `@require_session` decorator | ~20 min |
| 15 | CQ-05 | Use `with` statement for all DB connections | ~20 min |
| 16 | CQ-03 | Guard `filename` param before `os.path.join` | ~5 min |
| 17 | SEC-15, CQ-20 | Run `pip-audit`; lock transitive deps with hashes | ~30 min |
| 18 | CQ-21 | Move upload folder out of `/tmp` | ~5 min |

### Low Priority — Maintainability and Hygiene

| Step | Finding(s) | Action | Effort |
|---|---|---|---|
| 19 | CQ-17 | Write `pytest` test suite with `test_client` | ~2–4 hours |
| 20 | CQ-12 | Move admin query into `db.get_all_users()` | ~10 min |
| 21 | CQ-14 | Set `conn.row_factory = sqlite3.Row` | ~5 min |
| 22 | CQ-16 | Anchor `DATABASE` path to `__file__` | ~2 min |
| 23 | CQ-13 | Remove duplicate `logging.basicConfig` from `auth.py` | ~2 min |
| 24 | CQ-15 | Add type annotations and docstrings | ~30 min |

---

## Before-and-After Validation Checklist

Use this checklist after applying fixes to verify each remediation without running a
full security audit. All items can be validated by code inspection or with basic
`curl`/`pytest` commands against a locally running instance.

### Security Fixes

- [ ] **SEC-01 / SEC-02** — SQL queries in `db.py` use `?` placeholders only; no `+` or
  `%s` string interpolation remains in any `cursor.execute()` call.
- [ ] **SEC-03 / SEC-06** — `import pickle` is removed from `auth.py`. Session tokens
  are validated with `itsdangerous.URLSafeTimedSerializer`. A tampered token returns 401.
- [ ] **SEC-04** — `download_file` computes `os.path.abspath` of the resolved path and
  asserts it starts with `os.path.abspath(UPLOAD_FOLDER)`. Request with
  `filename=../../etc/passwd` returns 400.
- [ ] **SEC-05** — `hash_password` uses `bcrypt.hashpw`. `hashlib.md5` is no longer
  referenced in `auth.py`. Existing MD5-hashed passwords in the database have been
  migrated or the database has been reset.
- [ ] **SEC-07** — `config.py` contains no string literals for `SECRET_KEY`,
  `ADMIN_PASSWORD`. Application raises `KeyError` on startup when those env vars are unset.
- [ ] **SEC-08** — No log statement in `auth.py` or `app.py` references the `password`
  variable as a format argument.
- [ ] **SEC-09** — `/admin` reads credentials from the `Authorization` header, not
  `request.args`.
- [ ] **SEC-10** — `SELECT` in `/admin` (or `db.get_all_users()`) does not include
  the `password` column.
- [ ] **SEC-11** — `upload_file` calls `werkzeug.utils.secure_filename`. Files with
  extensions outside the allowlist return 400. `MAX_CONTENT_LENGTH` is set.
- [ ] **SEC-12** — `config.py` reads `DEBUG` from `os.environ`. `app.run` does not
  pass `host="0.0.0.0"` in non-development environments.
- [ ] **SEC-13** — `/login` has a rate-limit decorator. More than 5 requests/minute
  from the same IP returns 429.
- [ ] **SEC-14** — Resolved by SEC-03/SEC-06 fix. Verified by forging a token manually
  and confirming 401 is returned.
- [ ] **SEC-15** — `pip-audit -r requirements.txt` exits with code 0 (no known CVEs).

### Code-Quality Fixes

- [ ] **CQ-01** — `/download` returns 404 for missing file, 400 for missing param, 500
  for unexpected errors. No route returns 200 on an error path.
- [ ] **CQ-02** — All routes use `request.get_json(silent=True)`. Missing fields return
  400 with a descriptive JSON error, not an HTML 500.
- [ ] **CQ-03** — `/download` returns 400 immediately when `filename` is absent.
- [ ] **CQ-04** — No bare `except:` remains in `app.py`. Each catch names a specific
  exception type.
- [ ] **CQ-05** — All functions in `db.py` use `with sqlite3.connect(...) as conn:` or
  equivalent `try/finally`.
- [ ] **CQ-11** — Session check is implemented as a single `@require_session` decorator.
  The 6-line block does not appear more than once in `app.py`.
- [ ] **CQ-12** — `admin_panel` calls `db.get_all_users()`. No raw `cursor.execute`
  appears in `app.py`.
- [ ] **CQ-13** — `logging.basicConfig` appears exactly once, in `app.py`.
- [ ] **CQ-14** — `conn.row_factory = sqlite3.Row` is set in `get_connection()`.
  No `user[0]`, `user[1]` positional access remains in callers.
- [ ] **CQ-16** — `config.DATABASE` uses `os.path.abspath` relative to `__file__`.
- [ ] **CQ-17** — `pytest` runs with at least one happy-path and one error-path test
  per route. `pytest` exits with code 0.
- [ ] **CQ-20** — `requirements.txt` was generated by `pip-compile --generate-hashes`.
  All entries include `--hash=sha256:...` annotations.
- [ ] **CQ-21** — `UPLOAD_FOLDER` does not contain `/tmp`. Value is configurable via
  environment variable.

---

## Unverified Claims

The following are explicitly flagged as unverified. No finding above relies on these
claims; they are documented for completeness and to guide follow-up testing.

1. **Werkzeug debugger PIN derivability (SEC-12)** — The PIN weakness is a publicly
   documented attack technique, but confirming it requires knowing the server's
   `machine-id`, MAC address, and runtime username — values not visible in source code.

2. **SQLite `UNION SELECT` cross-table scope (SEC-02)** — Confirmed that string
   concatenation is used. Whether `ATTACH DATABASE` or `load_extension` are available
   depends on SQLite compile-time options on the target host.

3. **Write-side path traversal via `file.filename` (SEC-11)** — `os.path.join` behavior
   with `../` in a multipart filename is OS-dependent. Flask's multipart parser may strip
   path separators from `file.filename` on some platforms. Requires runtime verification.

4. **Specific CVEs for Flask 2.3.3 / Werkzeug 2.3.7 (SEC-15)** — These are older
   releases. No specific CVE is asserted because no authoritative advisory database was
   queried. Run `pip-audit` for a definitive result.

5. **`/tmp` world-writability (CQ-21)** — True on standard macOS and Linux but depends
   on the specific host OS configuration and mount options.

---

*This report was produced by AI-assisted static analysis (Kiro CLI) via source-code
inspection only. No application was executed, no HTTP requests were sent, no payloads
were delivered, and no application files were modified. This report is not a certified
security audit and does not guarantee that all vulnerabilities have been identified.
Findings should be validated by a qualified security engineer before use in a compliance
or production-readiness context.*
