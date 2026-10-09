# InternFlow database design

## Storage ownership

SQL is the source of truth for structured entities and workflow state. MongoDB, when enabled, preserves a flexible document mirror. The default local mode keeps JSON documents in the relational outbox, so the full application remains usable without a second server.

The schema is defined once in backend/models.py and compiled for SQLite or PostgreSQL. SQLite enables PRAGMA foreign_keys=ON for every connection. PostgreSQL uses psycopg.

## Core ER model

~~~mermaid
erDiagram
    BRANCHES ||--o{ STUDENTS : categorizes
    STUDENTS ||--o{ STUDENT_SKILLS : possesses
    SKILLS ||--o{ STUDENT_SKILLS : belongs_to
    STUDENTS ||--o{ PROJECTS : creates
    STUDENTS ||--o{ PREFERENCES : chooses
    COMPANIES ||--o{ INTERNSHIPS : offers
    INTERNSHIPS ||--o{ INTERNSHIP_SKILLS : requires
    SKILLS ||--o{ INTERNSHIP_SKILLS : belongs_to
    INTERNSHIPS ||--o{ INTERNSHIP_BRANCHES : accepts
    BRANCHES ||--o{ INTERNSHIP_BRANCHES : belongs_to
    INTERNSHIPS ||--o{ TIMELINE_EVENTS : schedules
    STUDENTS ||--o{ APPLICATIONS : submits
    INTERNSHIPS ||--o{ APPLICATIONS : receives
    APPLICATIONS ||--o{ APPLICATION_HISTORY : records
    STUDENTS ||--o{ BOOKMARKS : saves
    INTERNSHIPS ||--o{ BOOKMARKS : is_saved
    INTERNSHIPS ||--o{ INGESTIONS : has_source
~~~

## Tables and keys

| Table | Purpose | Important keys / constraints |
|---|---|---|
| students | Student identity, academic eligibility, experience | PK id; unique email; FK branch; CGPA/year/experience checks |
| branches | Branch catalog | PK name; normalized uppercase |
| skills | Shared skill catalog | PK id; unique name |
| student_skills | Student ↔ skill junction | Composite PK/FKs student_id + skill_id |
| projects | Student projects and domain evidence | PK id; FK student_id |
| preferences | Student domain/location preferences | FK student_id; unique student + kind + value; allowed kinds |
| companies | Shared company catalog | PK id; unique name |
| internships | Role, pay, location, eligibility criteria | FK company_id; unique company + role + location; CGPA/pay/duration/mode checks |
| internship_skills | Internship ↔ skill junction | Composite PK/FKs internship_id + skill_id |
| internship_branches | Eligible branches, one row per branch | Composite PK/FKs internship_id + branch_name |
| timeline_events | Deadline, OA, and PPT timestamps | FK internship_id; unique internship + event kind; allowed kinds |
| bookmarks | Student shortlist | Composite PK/FKs student_id + internship_id |
| applications | Status, cover letter, notes | FKs student_id/internship_id; unique student + internship; allowed statuses |
| application_history | Immutable-by-API status events | FK application_id; before/after status and timestamp |
| documents | Transactional JSON outbox | UUID PK; document kind and payload |
| ingestions | Source deduplication and provenance | FK internship_id; unique SHA-256 source hash; document UUID reference |

No rows in internship_branches means any branch is eligible. The UI accepts a comma-separated branch field for convenience; the database converts it into separate catalog and junction rows. Skills follow the same principle.

## Normalization

Each business row contains one entity, relationship, or event. Skills and eligible branches are not repeated as lists in entity columns. Composite junction keys remove duplicate associations. Company details live in companies rather than repeating in every internship. Event dates are separated from role attributes, and status history is separated from current application state.

The flexible JSON outbox is intentionally denormalized document content, separate from the normalized business model. preferences stores one value per row rather than a list in the student row. The public API renders skill and branch arrays/strings for convenience.

## Transactions and concurrency

- Import: company/skills/branches → internship → junction rows → timeline → source document → ingestion hash commit together.
- Prepare: one application and its initial history row commit together. A unique constraint enforces one application per student/opportunity.
- Update: current status and history row commit together; notes and cover letter share the transaction.
- Profile: academic data and replacement skill/project/preference associations commit together.
- SQL constraint failures return HTTP 409; validation failures return HTTP 422.
- A repeat source hash is rejected. A different message for the same company/role/location also conflicts, avoiding silent overwrites. Announcement update/version reconciliation is future work.
- MongoDB writes happen after the SQL commit. Mirroring is idempotent by document UUID. SQL outbox records remain recoverable if MongoDB is offline; startup and explicit Sync retry them.

The local prototype is intended for one user. Production concurrent status editing needs optimistic version checks and an outbox worker with incremental delivery state. It does not claim exactly-once delivery across SQL and MongoDB.

## Indexes and integrity

Foreign keys enforce relationship integrity. Frequently read student_id, company_id, internship_id, application_id, document kind, event starts_at, and source hashes have indexes (some through PK/unique constraints). CHECK constraints protect numeric domains and allowed states. Cascading deletion is configured for owned relational records; the current API does not expose deletion.

Generated DDL is available in database/schema-postgresql.sql and database/schema-sqlite.sql. Examples in database/queries.sql match the UI’s named query API.

## Matching is a computed view

Scores are not saved as mutable facts: profile changes recompute them from relational data.

| Factor | Weight | Evidence |
|---|---:|---|
| Skills | 40 | Required skill coverage, case-insensitive aliases |
| Eligibility | 20 | CGPA, study year, allowed branch |
| Projects | 15 | 7.5 per relevant project, capped at 15 |
| Experience | 10 | Coverage of requested experience; full score if none requested |
| Preferred domain | 10 | Exact preferred domain membership |
| Location | 5 | Preferred location or Remote preference |

A failed hard eligibility check caps the final score at 49. Project relevance uses domain or keyword evidence, not a semantic LLM model. A strong match is an eligible, open opportunity scoring at least 80.

“Unlocking” a skill means crossing the 80% threshold in a simulation. It cannot override academic eligibility. The simulator does not modify the saved profile.

## Temporal conventions

Event timestamps are stored as naive **IST civil time** after normalizing input offsets. API responses include +05:30. Application/audit timestamps are stored as naive **UTC** and returned with UTC offsets. ICS export converts events to UTC and folds lines at 75 UTF-8 bytes. Production migrations should switch PostgreSQL timestamp columns to explicit timezone-aware types.

## Live SQL demonstration

The UI supports six predefined read-only queries: company join, skill demand aggregation, student application join, full eligibility filter with branch EXISTS, audit history, and ordered timeline events. It never executes arbitrary SQL supplied by a browser.

## Why NoSQL is useful here

Raw announcements vary in language and fields. Resume versions and AI extraction payloads evolve. Documents retain raw text, reviewed JSON, extraction mode, source hash, original filename, and variable context without expanding the relational schema for every provider or message format.

In SQLite-only mode this is a document-shaped JSON collection, not a claim that a NoSQL server is running. The optional MongoDB adapter uses a real MongoDB collection.
