# AIVOA.AI — AI-Powered Customer Complaint Management System

An AI-powered Customer Complaint Management System for pharmaceutical (API & FDF)
manufacturers, built for the AIVOA.AI Round 1 AI Product Engineer assignment.

It reproduces the reference UI: a **"Log Customer Complaint"** QMS form on the left and
an **AIVOA Copilot** chat panel on the right. You paste a raw customer email or drop a
complaint PDF into the Copilot, a LangGraph agent (backed by Groq) extracts the
structured fields, runs an AI risk assessment, and auto-fills the form. You can then
correct any field conversationally (e.g. *"ah sorry the batch number is BMX240602 and
affected quantity is 48 capsules"*) before committing the record to the QMS ledger.

---

## 1. Architecture

```
┌──────────────────────────┐        ┌────────────────────────────────────────────┐
│        FRONTEND          │  REST  │                   BACKEND                    │
│  React 18 + Redux Toolkit│◄──────►│              FastAPI (Python)                │
│  - ComplaintForm.jsx     │  JSON  │  routers/copilot.py   routers/complaints.py  │
│  - CopilotPanel.jsx      │        │        │                      │              │
│  - complaintSlice.js     │        │        ▼                      ▼              │
│  - chatSlice.js          │        │  agents/langgraph_agent.py   models/Complaint │
└──────────────────────────┘        │        │                      │              │
                                     │        ▼                      ▼              │
                                     │  LangGraph StateGraph:    SQLAlchemy ORM      │
                                     │  extract_entities                            │
                                     │      → assess_risk                           │
                                     │      → bonus_features                        │
                                     │      → compose_reply                         │
                                     │        │                                     │
                                     │        ▼                                     │
                                     │  Groq API (gemma2-9b-it /                    │
                                     │  llama-3.3-70b-versatile)                    │
                                     │  falls back to rule_based_fallback.py        │
                                     │  if no GROQ_API_KEY is set                   │
                                     └───────────────────────┬───────────────────────┘
                                                              ▼
                                                    Postgres / MySQL / SQLite
```

### Request flow (matches the demo video)

1. User pastes complaint text or drops a PDF into the Copilot panel.
2. Frontend calls `POST /api/copilot/parse` (multipart: `text` or `file`).
3. Backend extracts raw text (pypdf for PDFs) and runs it through the **LangGraph**
   extraction graph:
   - `extract_entities` — Groq `gemma2-9b-it` pulls structured fields out of free text.
   - `assess_risk` — Groq `llama-3.3-70b-versatile` classifies severity, suggests the
     next QA action, and drafts an initial risk assessment.
   - `bonus_features` — generates a completeness score, a CAPA recommendation, and a
     one-line summary (bonus AI features).
   - `compose_reply` — writes the chat-facing confirmation message.
4. The form on the left is populated from the response; the AI Copilot Risk
   Assessment box and CAPA box are populated from `risk` / `bonus`.
5. If a field is wrong, the user types a correction in the chat. Frontend calls
   `POST /api/copilot/chat` with the message + current fields; only the mentioned
   fields are updated (diff-based), same as the demo video's "ah sorry, the batch
   number is..." moment.
6. **Commit to QMS Ledger** calls `POST /api/complaints`, which persists the record,
   runs a simple duplicate check (same product + batch number), and returns a
   generated complaint reference (`CC-2026-XXXXX`).

### Why there's a rule-based fallback

`GROQ_API_KEY` requires creating a token at console.groq.com (per the assignment). So
the whole pipeline also runs on a deterministic, regex-based extractor
(`app/agents/rule_based_fallback.py`) whenever no key is configured or a Groq call
fails — this way the app is always demoable, and it's easy to prove the difference
once you drop in a real key (`groq_enabled` is reported at `GET /api/health`).

---

## 2. Project layout

```
aivoa-complaint-system/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── langgraph_agent.py     # the real LangGraph + Groq workflow
│   │   │   └── rule_based_fallback.py # offline fallback extractor
│   │   ├── models/complaint.py        # SQLAlchemy model
│   │   ├── schemas/complaint.py       # Pydantic request/response models
│   │   ├── routers/copilot.py         # /api/copilot/parse, /api/copilot/chat
│   │   ├── routers/complaints.py      # /api/complaints (commit, list, get)
│   │   ├── services/pdf_service.py    # PDF/email text extraction
│   │   ├── config.py, database.py, main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/ComplaintForm.jsx
│   │   ├── components/CopilotPanel.jsx
│   │   ├── components/StatusBadge.jsx
│   │   ├── store/complaintSlice.js
│   │   ├── store/chatSlice.js
│   │   ├── api/client.js
│   │   └── styles/index.css
│   ├── package.json, vite.config.js, index.html
│   └── .env.example
├── demo_data/
│   ├── sample_email_complaint.txt     # pasteable demo complaint
│   └── sample_complaint_report.pdf    # uploadable demo complaint PDF
└── README.md
```

---

## 3. Setup & run

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Postgres or MySQL instance (or just use the SQLite default — zero setup)
- A free Groq API key from https://console.groq.com (optional — app works without it)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env:
#   - Add GROQ_API_KEY for live AI extraction (leave blank to use the offline fallback)
#   - Set DATABASE_URL to your Postgres/MySQL instance, or leave the sqlite default

uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000` (interactive docs at `/docs`).
Tables are auto-created on startup via `Base.metadata.create_all`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env    # optional — Vite already proxies /api -> localhost:8000 in dev
npm run dev
```

Open `http://localhost:5173`.

### Try it end-to-end

1. Open the app — the form shows **"Pending Triage."**
2. Paste the contents of `demo_data/sample_email_complaint.txt` into the Copilot input
   (or drag-and-drop `demo_data/sample_complaint_report.pdf`) and hit send.
3. Watch the form auto-fill and the AI Copilot Risk Assessment box populate; status
   flips to **"Ready to Commit."**
4. Try a correction, e.g.: `ah sorry the batch number is BMX240602 and affected
   quantity is 48 capsules` — only those two fields update.
5. Click **Commit to QMS Ledger** — status flips to **"Committed"** with a generated
   complaint reference. Check `GET /api/complaints` to see it persisted.

---

## 4. Mandatory stack checklist

| Requirement | Where |
|---|---|
| React + Redux | `frontend/src/store/*`, all components use `useSelector`/`useDispatch` |
| Python + FastAPI | `backend/app/main.py`, `routers/*` |
| LangGraph | `backend/app/agents/langgraph_agent.py` — `StateGraph` with 4 nodes |
| Groq (`gemma2-9b-it`, `llama-3.3-70b-versatile`) | `backend/app/agents/langgraph_agent.py` — `_call_groq_json` |
| MySQL / Postgres | `backend/app/database.py` via `DATABASE_URL` (SQLAlchemy) |
| Google Inter font | `frontend/index.html` (Google Fonts link) + `styles/index.css` |

## 5. Bonus AI features implemented

- **Complaint Completeness Checker** — `ai_completeness_score` (0–100) shown under the
  risk box.
- **CAPA Recommendation** — `ai_capa_recommendation`, a numbered corrective/preventive
  action plan.
- **Complaint Summary** — `ai_summary`, one-line summary generated per complaint.
- **Duplicate Complaint Detection** — `POST /api/complaints` checks for an existing
  complaint with the same product + batch number and flags `ai_duplicate_of`.
- **AI Risk Classification** — `ai_severity` (Minor/Major/Critical) +
  `ai_suggested_next_action`.

## 6. Notes on the demo PDFs/emails

Per the assignment, these are fictional pharmaceutical complaint documents created for
demonstration only (`demo_data/`), not real customer data.

## 7. What's stubbed vs. production-grade (documented per the brief's own scope)

- PDF/email parsing uses `pypdf` text-layer extraction, not OCR (explicitly not
  required by the assignment).
- The rule-based fallback extractor is intentionally simple regex matching — it exists
  purely so the app is fully runnable without a Groq key; the actual required AI path
  is the LangGraph + Groq workflow in `langgraph_agent.py`.
