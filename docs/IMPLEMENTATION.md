# Implementation notes

## Architecture

Browser → React/Vite → FastAPI → SQLAlchemy → SQLite or PostgreSQL.

Extraction → local parser or opt-in LangChain structured output → user review → relational write + JSON outbox → optional MongoDB mirror.

Matching reads the reviewed relational profile and requirements. Applications, saves, and dates persist in SQL. Shared UI state refreshes after mutations.

## Endpoints

| Method | Path | Behavior |
|---|---|---|
| GET | /api/health | Relational/document/AI modes, IST clock |
| GET / PUT | /api/profile | Read/update student profile |
| GET | /api/internships | Ranked opportunities and explanations |
| POST | /api/internships/{id}/bookmark | Toggle persistent save |
| POST | /api/internships/{id}/prepare | Idempotently prepare an application |
| GET | /api/applications | Pipeline, answers, history |
| PATCH | /api/applications/{id} | Atomic status/history, letter, notes |
| GET | /api/dashboard | Derived counts, timelines, reminders |
| GET | /api/calendar | IST events |
| GET | /api/calendar/export | RFC 5545 ICS with alarms |
| GET | /api/notifications | Three-day reminders |
| POST | /api/extract/announcement | Extraction without import |
| POST | /api/ingestions | Reviewed import with provenance |
| POST | /api/extract/resume | PDF/TXT extraction without profile overwrite |
| GET | /api/skill-gaps | Demand ranking and stateless simulation |
| GET | /api/database | Schema, counts, documents, query catalog |
| POST | /api/database/queries/{name} | Whitelisted read-only example |
| POST | /api/database/sync | MongoDB mirror recovery |
| GET | /api/export | JSON data export |

## Verification

Backend tests use a temporary database and real FastAPI TestClient. They cover foreign keys, matching/eligibility, persistence, application constraints/history, profile-driven score updates, import deduplication, calendar reminders/encoding, whitelisted SQL, resume review, validation, and AI configuration errors.

Frontend tests use Vitest, React Testing Library, jsdom, and fixtures generated through the real API. They cover search/saving, match details, application review, announcement import, profile editing, skill simulation, SQL results, calendar export, and disconnected-server handling.

17 backend tests and 9 UI interaction tests passed. The Vite production build and Docker Compose configuration validation passed. No connected browser was available in the build session, so screenshots, visual layout QA, and browser-level end-to-end checks remain unverified. Responsive CSS and native dialog behavior need a real-device pass.

Docker Desktop’s daemon was unavailable. PostgreSQL DDL is compiled from the actual models and compose configuration is supplied; live PostgreSQL/MongoDB operations have not been verified. LangChain requires provider credentials and has not been exercised against a live model.

## Operational behavior

- Default SQLite data persists and is ignored by Git; seeding happens once.
- Tests and fixture generation use temporary databases.
- Imports retain original text and reviewed JSON.
- AI is disabled by default and opted into per extraction.
- Uploads: 8 MB maximum, 30 PDF pages, text truncated at 30,000 characters for extraction.
- File names are sanitized; uploaded files are not stored or executed.
- Unknown API paths return JSON 404.
- FastAPI serves built React assets on the same origin.
- Document storage mode is labeled accurately.
- The browser supplies query names, never arbitrary SQL.
- Status changes never make external application submissions.
- Default listeners and Docker published ports use loopback.

## Next iterations

1. Real desktop/mobile browser QA and accessibility contrast audit.
2. Multi-student authentication, student/admin roles, and data authorization.
3. Versioned migrations and timezone-aware PostgreSQL columns.
4. Scheduled opt-in email/push reminders with delivery receipts.
5. Richer free-form extraction, OCR, and better project relevance.
6. Reviewed announcement revisions and event rescheduling.
7. Incremental MongoDB outbox worker, retry state, and retention.
8. Institution-controlled sources and permitted ingestion integrations.
