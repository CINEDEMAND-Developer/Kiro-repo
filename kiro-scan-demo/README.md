# kiro-scan-demo

A deliberately vulnerable Flask REST API used to demonstrate AI-assisted code
review and security scanning.

**DO NOT deploy this application anywhere.** It contains intentional security
vulnerabilities for demonstration purposes only.

## Quick start

```bash
pip install -r requirements.txt
python app.py
```

## Endpoints

| Method | Path             | Description                        |
|--------|------------------|------------------------------------|
| POST   | /register        | Create a new user account          |
| POST   | /login           | Authenticate and get session token |
| GET    | /notes           | List notes for the logged-in user  |
| POST   | /notes           | Create a new note                  |
| GET    | /notes/search?q= | Search notes by title keyword      |
| POST   | /upload          | Upload a file                      |
| GET    | /download        | Download a file by name            |
| GET    | /admin           | Admin panel (lists all users)      |

## Authentication

After a successful `/login` the response contains a `session` field.
Pass this value in the `X-Session-Token` header for authenticated requests.
