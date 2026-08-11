# intelligence_core Worklog & Handoff

Last updated: 2026-08-11
Branch: feature/intelligence-core

Purpose
-------
This document is a living worklog and handoff for the intelligence_core Phase‑1 implementation. It records what has been implemented, what remains to be done, tests and run instructions, design decisions, and next steps so another developer can pick up where work left off.

Status summary
--------------
Completed (committed on feature/intelligence-core):
- App initialization
  - intelligence_core/__init__.py
  - intelligence_core/apps.py (AppConfig that wires signals)

- Core models
  - intelligence_core/models.py
    - StudentIntelligenceProfile
    - Evidence (UUID primary key)
    - MasteryRecord

Work in progress / planned (remaining for Phase 1):
- Create migrations for the above models (pending commit)
- Implement signal handlers to convert ItemAttempt and StudentScore saves into sanitized Evidence rows
- Implement process_evidence Celery task (with a synchronous fallback for local/dev)
- Deterministic Mastery Engine (recency decay, difficulty weighting, evidence-type multiplier)
- API endpoints:
  - GET /api/intelligence/profiles/{user_id}/
  - POST /api/intelligence/recompute/{user_id}/
- Synthetic fixtures and unit/integration tests (signals, mastery math, end‑to‑end flow)
- Docs/runbook (Redis + Celery startup, migrations, retention & PII notes)
- Open draft PR (reviewers: alice,bob; labels: enhancement,needs-review)

Design decisions & conventions
------------------------------
- Concept IDs: domain:slug format (e.g., "maritime:man-overboard").
- Evidence ID: UUID primary key for traceability across systems.
- Evidence.payload stores structured, sanitized activity data (avoid PII by default).
- MasteryRecord.evidence_refs stores a list of contributing evidence UUIDs.
- Redis is the recommended Celery broker. A synchronous fallback will be added to run without Redis for CI/local dev.
- LLM calls are out of the Phase‑1 core loop. ProviderAdapter pattern will be added later.
- Default retention policy (configurable): keep structured Evidence indefinitely; archive raw logs/payloads after 90 days.

How to continue (step-by-step)
------------------------------
1) Create & run migrations
   - Ensure intelligence_core is added to INSTALLED_APPS.
   - Run: python manage.py makemigrations intelligence_core
   - Run: python manage.py migrate

2) Implement signals
   - File: intelligence_core/signals.py (create)
   - Connect ItemAttempt.post_save and StudentScore.post_save.
   - For each saved object:
     - Locate or create StudentIntelligenceProfile for the user.
     - Create an Evidence record with sanitized payload and source metadata.
     - Enqueue process_evidence task with evidence.id.
   - Add a sanitization hook function (intelligence_core.utils.sanitize_payload) to remove PII; keep it simple and configurable.

3) Implement processing task & Mastery Engine
   - File: intelligence_core/tasks.py
   - Provide process_evidence(evidence_id) Celery task.
   - Task should:
     - Load Evidence and identify concept tags in payload.
     - For each concept, load or create MasteryRecord, compute new mastery using deterministic formula:
       mastery = normalized(sum(correctness * difficulty * evidence_multiplier * recency_factor) / max_possible)
     - Update MasteryRecord.mastery_score, uncertainty and evidence_refs.
     - Update StudentIntelligenceProfile.overall_mastery (aggregate)
     - Persist provenance log (task run id, commit hash if possible)
   - Provide synchronous fallback: tasks.run_process_evidence_sync(evidence_id) for CI without Celery.

4) API
   - File: intelligence_core/views.py and urls.py
   - Implement GET profile endpoint and POST recompute endpoint (admin-only) that triggers recomputation via Celery or sync fallback.

5) Tests & fixtures
   - Add synthetic fixtures under intelligence_core/fixtures/
   - Unit tests: intelligence_core/tests/test_mastery.py (math), test_signals.py
   - Integration test: test_end_to_end.py creating an ItemAttempt, asserting Evidence created, run process_evidence sync, then check MasteryRecord and profile via API.

6) Runbook & docs
   - Add intelligence_core/WORKLOG.md (this file) and intelligence_core/README.md with high-level usage, CLI commands to recompute all profiles, and notes on PII redaction.

Developer notes / gotchas
-------------------------
- Be careful with imports in signals (avoid circular imports). Use Django's get_model or import within handler.
- Evidence.payload must not contain raw PII. Use a small, well‑documented sanitizer function and place hooks for domain-specific redaction.
- Task idempotency: process_evidence should be safe to run multiple times for same evidence id (e.g., deduplicate evidence_refs).
- When updating MasteryRecord.evidence_refs, ensure you merge UUIDs without duplicates.
- Tests should run without Redis/Celery using the synchronous fallback.

Useful file references (in branch feature/intelligence-core)
-----------------------------------------------------------
- intelligence_core/models.py  (core models)
- intelligence_core/apps.py    (AppConfig wiring signals)
- intelligence_core/__init__.py (app init)

Planned files to be added
------------------------
- intelligence_core/migrations/0001_initial.py  (generated by makemigrations)
- intelligence_core/signals.py
- intelligence_core/tasks.py
- intelligence_core/utils.py (sanitize_payload and helpers)
- intelligence_core/views.py, urls.py, serializers.py
- intelligence_core/tests/* (unit/integration)
- intelligence_core/fixtures/*
- intelligence_core/README.md (short usage)

Acceptance criteria for Phase 1
-------------------------------
- ItemAttempt or StudentScore triggers Evidence creation via signals.
- process_evidence updates MasteryRecord and StudentIntelligenceProfile.overall_mastery deterministically.
- API endpoints expose profile and masteries.
- Unit & integration tests cover the main flows and run in CI without Redis.

Contacts & handoff
------------------
- Current assignee: Copilot agent (automated changes pushed to feature/intelligence-core).
- Reviewers intended for the draft PR: alice, bob.
- If you pick up work: follow the step-by-step section above. When committing, reference this worklog and add progress notes with commit messages.

Next immediate commit planned
-----------------------------
- Add migrations for models (makemigrations) and commit the migration file.

Commit checklist (what I will push in the next commits)
------------------------------------------------------
- intelligence_core/migrations/0001_initial.py
- intelligence_core/signals.py
- intelligence_core/utils.py
- intelligence_core/tasks.py
- intelligence_core/views.py, urls.py, serializers.py
- intelligence_core/tests/test_mastery.py, test_signals.py, test_end_to_end.py
- intelligence_core/README.md

If you take over
----------------
- Read this WORKLOG.md first.
- Run tests locally with: python manage.py test intelligence_core
- Use the sync fallback to iterate quickly: call the sync helper in tasks rather than running a Celery worker.

