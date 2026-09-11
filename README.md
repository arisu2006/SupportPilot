# SupportPilot — Premium AI Support Desk

AI-assisted IT ticket desk with knowledge retrieval, cited resolutions, and JWT auth.

## Features

- **JWT authentication** (PyJWT) — register / login / protected routes
- Premium light dashboard
- Submit ticket → classify + full RAG result **in the same tab**
- Tickets stored in SQLite (`tickets.db`) and listed under **Tickets**
- One-click Google demo sign-in

## Run

```bash
cd SupportPilot_M2
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## JWT (as in the JWT PPT)

| Action | Method | Path | Notes |
|--------|--------|------|--------|
| Register | POST | `/register` or `/api/register` | JSON: `email`/`username`, `password` |
| Login | POST | `/api/login` | Returns `{ "token": "<JWT>" }` |
| Profile | GET | `/profile` or `/api/profile` | Header: `Authorization: Bearer <token>` |
| Me | GET | `/api/auth/me` | Same, cookie or Bearer |

Example:

```bash
# Register
curl -X POST http://127.0.0.1:5000/register -H "Content-Type: application/json" \
  -d '{"username":"saranya","password":"mypassword123","email":"saranya@company.com"}'

# Login → token
curl -X POST http://127.0.0.1:5000/api/login -H "Content-Type: application/json" \
  -d '{"username":"saranya","password":"mypassword123"}'

# Protected profile
curl http://127.0.0.1:5000/profile -H "Authorization: Bearer <token>"
```

UI login also sets an `sp_token` cookie (same JWT).

## Tickets

- Submit from **Submit Ticket** tab → always saved to SQLite
- Classification + RAG workflow + resolution shown **on the same tab**
- **Tickets** tab lists all stored tickets (refreshes after submit)

## API

```
POST /api/ticket          Create + RAG (JWT required)
GET  /api/tickets         List tickets
GET  /api/ticket/<id>     Ticket detail
POST /api/rag             Ad-hoc RAG only
```
