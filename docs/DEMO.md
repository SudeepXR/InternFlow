# A five-minute InternFlow demo

1. **Discover.** Show counts, match-ranked opportunities, saves, and upcoming dates. Explain that initial listings are fictional.
2. **Explain a match.** Open Microsoft or Razorpay and show the six weighted factors. Open NVIDIA to demonstrate the CGPA hard gate and 49% score cap.
3. **Import a message.** Announcement inbox → Try a sample → Extract opportunity. Edit a field, verify dates, then Confirm & import. Find the new opportunity in Discover and its dates in Calendar. Repeat the import to show deduplication.
4. **Prepare an application.** Open the new opportunity → Prepare application. Review profile-based form answers, edit/download the cover letter, and add notes. Explain that submission happens independently. Mark applied, move to Assessment or Interview, then inspect Status history.
5. **Analyze a resume.** My profile → download sample TXT → upload it → review extraction → add to editable form. Add AWS/Docker and save; demonstrate recalculated matches. The optional LangChain checkbox requires configured credentials.
6. **Explore a skill roadmap.** Select Docker and AWS. Show before/after scores and newly strong matches without changing the saved profile. Eligibility stays enforced.
7. **Manage timelines.** Show Deadline, OA, and PPT labels, month navigation, date selection, watched filtering, and ICS export with one-day reminders. In-app reminders cover the next three days.
8. **Show the database.** Click entities in the ER diagram, inspect PK/FK/check constraints, show junction tables, run skill aggregation and application joins, inspect status history, and open the raw source document.

When running Docker, point out PostgreSQL and MongoDB. In local mode, describe SQLite + JSON outbox accurately.

## Viva points

- Why skills and branches use junction tables.
- Why current application state and history are separate.
- How a failed partial import rolls back the SQL transaction.
- How unique constraints prevent duplicate applications.
- Why resume/message payloads suit flexible document storage.
- How the SQL outbox recovers from unavailable MongoDB.
- Why eligibility is a gate rather than only an additive factor.
- Why the system prepares reviewed drafts rather than claiming to submit external forms.
