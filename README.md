# InternFlow

An internship intelligence and application assistance platform for a DBMS course. Turn a pasted announcement into a reviewed opportunity, match it against your resume, track applications and dates, and see which skills improve your options.

React + Vite frontend · FastAPI backend · SQLAlchemy relational model · SQLite by default · optional PostgreSQL, MongoDB, and LangChain.

## Run it

Requires Node.js 22+ and Python 3.11+.

From this project folder:

~~~powershell
npm run setup
npm start
~~~

Open **http://127.0.0.1:8000**. API documentation: **http://127.0.0.1:8000/docs**.

Dependencies are already installed in this workspace, so **npm start** is enough here. Stop any existing process on port 8000 before starting a second copy.

On Windows, you can also double-click **start-internflow.cmd**. The launcher installs dependencies, builds React, and starts the app. Keep its console open while using the app.

For development with live reload:

~~~powershell
npm run dev
~~~

React: http://127.0.0.1:5173 · API: http://127.0.0.1:8000. Vite proxies API requests automatically.

## What works

- Discovery with search, domain/location/eligibility filters, match/deadline/stipend sorting, and grid/list views.
- Persistent saved opportunities.
- Six-factor match explanations, with a hard eligibility gate for CGPA, year, and branch.
- Application drafts with editable cover letters, profile-based answers, notes, downloads, and manual submission tracking.
- Application pipeline with status history written atomically.
- Calendar with deadline, OA, and PPT events, watched-opportunity filtering, and ICS export with reminders.
- In-app reminders for the next three days. These are computed when the app loads; external push/email delivery is not implemented.
- Resume upload for text-based PDF and UTF-8 TXT files, extraction review, and editable student profiles.
- Announcement extraction, editable review, atomic import, source preservation, and duplicate detection.
- Skill gap ranking and a what-if simulator that does not change your saved profile.
- Database explorer with an ER diagram, all 16 tables, foreign keys, constraints, named SQL examples, and raw documents.
- JSON export of profile, applications, and saved opportunities.

The initial student and all 12 sample internships are fictional. Sample company names illustrate the UI; deadlines and stipends are not actual hiring information. Dates are relative to the first startup. Replace the demo profile and import your own announcements.

## Your RDBMS requirement

The default app uses **SQLite, a real relational database**, with foreign-key enforcement, joins, indexes, composite primary keys, unique/check constraints, and transactions. It stores data on disk in **backend/data/internflow.db**. PostgreSQL uses the same schema and API.

The schema includes students, branches, companies, internships, skills, three relationship tables, projects, preferences, timelines, bookmarks, applications, status history, ingestion metadata, and a document outbox. See [the database design](docs/DATABASE.md), [PostgreSQL DDL](database/schema-postgresql.sql), and [SQLite DDL](database/schema-sqlite.sql).

## PostgreSQL + MongoDB with Docker

Start Docker Desktop first. Stop the local server on port 8000, then run:

~~~powershell
docker compose up --build
~~~

Open http://127.0.0.1:8000. This runs the entire app with PostgreSQL as its RDBMS and MongoDB as its document mirror. Data persists in Docker volumes. Development database passwords in compose.yaml are for this local course demo.

If you prefer databases in Docker and the app on your machine:

~~~powershell
docker compose up -d postgres mongodb
npm run setup -- --integrations
Copy-Item .env.example .env
~~~

Set these values in .env:

~~~dotenv
DATABASE_URL=postgresql+psycopg://internflow:internflow_dev@127.0.0.1:5432/internflow
MONGODB_URI=mongodb://internflow:internflow_dev@127.0.0.1:27017/internflow?authSource=admin
~~~

Then run npm start. Database URLs are read from .env; never commit actual credentials.

SQLite JSON is the local fallback for documents. With MongoDB configured, the app retains a transactional SQL outbox and mirrors it into the MongoDB documents collection. A failed MongoDB write leaves the SQL record intact. Use **Database explorer → Document store → Sync MongoDB** to retry.

## Optional LangChain extraction

Local rules work without credentials. They recognize labeled announcement fields, common skills, ISO/named dates, and basic resume fields; ambiguous or missing details need review. This mode is labeled explicitly and does not pretend to be an LLM.

To enable the implemented LangChain integration:

~~~powershell
npm run setup -- --integrations
Copy-Item .env.example .env
~~~

Set ENABLE_AI=true, OPENAI_API_KEY, and OPENAI_MODEL in .env, then restart. Use the **Use LangChain extraction** checkbox on the resume or inbox page. The checkbox is off by default. Enabling it sends the provided text to the configured AI provider and may incur API costs.

The pipeline extracts text → invokes ChatOpenAI with a Pydantic structured-output schema → validates JSON → presents a review → saves reviewed structured data. Scanned PDF OCR is not included.

## Checks

~~~powershell
npm test
npm run test:api
npm run build
~~~

Backend tests run in a temporary SQLite database and do not touch your demo data. Frontend tests use fixtures produced through the real API, and exercise student interactions in a virtual DOM.

To regenerate schema SQL or frontend fixtures:

~~~powershell
.\.venv\Scripts\python.exe scripts/export-schema.py
.\.venv\Scripts\python.exe scripts/create-test-fixtures.py
~~~

## Project layout

~~~text
src/                 React interface, workflow components and UI tests
backend/             FastAPI routes, relational models, extraction and matching
backend/tests/       API and integrity tests
database/            Generated SQLite/PostgreSQL DDL and query examples
scripts/             Setup, startup, development and test helpers
docs/                Architecture, DBMS design, demo script and implementation notes
compose.yaml         PostgreSQL, MongoDB and full app configuration
~~~

## Current scope

This is a **single-student, local course prototype**. Authentication, separate student accounts, admin moderation, background email/push scheduling, automatic WhatsApp/job-board ingestion, and external form submission are future iterations. The app prepares drafts for review, as requested; it does not submit applications.

Bind to localhost for this version. Hosted production use needs authentication, authorization, migrations, upload hardening, and operational controls. Existing user data is never reset on startup; seeding happens only when the initial student is absent.

See [the demo walkthrough](docs/DEMO.md) and [implementation notes](docs/IMPLEMENTATION.md) for a presentation-ready tour and verification details.
