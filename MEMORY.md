# Memory.md — DeployMe Project Context

## Project Identity
- **Name**: DeployMe
- **Tagline**: Deploy yourself into the job market
- **What it is**: A RAG-based web app that analyzes tech job listings, helps users optimize their CVs for specific roles, and tracks their application pipeline
- **Who it's for**: CS students and junior developers applying for internships and entry-level roles in the German tech market
- **Why it exists**: Portfolio project for AI/ML internship applications. Also intended to be genuinely useful to real users
- **Repo folder name**: `deployme/`

## Architecture Decisions (Already Made)

- **Monorepo structure**: `backend/` and `frontend/` in the same repo
- **Backend**: FastAPI (Python). Not Django, not Flask
- **Frontend**: React + Vite + TailwindCSS. Not Next.js, not Vue
- **Vector store**: ChromaDB (local, persisted to disk). Not Pinecone, not Weaviate. Used for job listings only
- **Embeddings**: sentence-transformers `all-MiniLM-L6-v2` (runs locally). Not OpenAI embeddings
- **LLM**: Anthropic API (claude-sonnet-4-20250514). Not OpenAI
- **Auth and user data**: Supabase (hosted PostgreSQL + auth). Used for authentication and the application tracker table. NOT used for job listings or ChromaDB data
- **PDF parsing**: PyMuPDF (fitz). Not pdfplumber, not PyPDF2
- **Charts**: Recharts. Not D3, not Chart.js
- **Rate limiting**: slowapi. Not custom middleware
- **Input sanitization**: Pydantic models for validation, custom sanitizer for prompt injection defense
- **Containerization**: Docker Compose for backend + frontend + ChromaDB. Supabase is hosted externally

## Security Rules (Non-Negotiable)

These rules apply to every piece of code written in this project. No exceptions.

### Secrets
- `.env` is in `.gitignore`. Check this before every commit
- Never hardcode API keys, tokens, or passwords anywhere in the codebase
- Never log full API keys or the Supabase service role key. If logging is needed, log only the last 4 characters
- Never send API keys or secrets to the frontend. All LLM calls are server-side only
- Use pydantic BaseSettings in `core/config.py` to load all config from `.env`
- `docker-compose.yml` reads from `.env`, never contains inline secrets

### Supabase Key Rules (Critical)
- **Anon key**: public, safe for frontend. Used in `frontend/src/services/supabase.js`
- **Service role key**: secret, backend only. Used in `backend/core/supabase_client.py`. This key bypasses Row Level Security — treat it like a database root password
- The service role key must NEVER:
  - Be prefixed with `VITE_` (Vite exposes all VITE_ vars to the browser bundle)
  - Appear in any frontend file
  - Be logged, printed, or included in any API response
  - Be committed to git, even in test files or comments
- If you ever need to reference which key is which, add a code comment. Example:
  ```python
  # IMPORTANT: This uses the SERVICE ROLE KEY (server-side only, bypasses RLS)
  ```
  ```javascript
  // IMPORTANT: This uses the ANON KEY only (public, safe for frontend, respects RLS)
  ```

### Input Validation
- Every endpoint uses a Pydantic model for request validation. No raw dicts
- All string inputs have max length constraints enforced at the Pydantic level
- File uploads are validated three ways: MIME type, file extension, and magic bytes
- Max file size for PDFs: 5MB
- Strip leading/trailing whitespace on all string inputs
- Reject requests that fail validation with a 422 and a clear error message

### Prompt Injection Defense
- All user-provided content sent to the LLM is wrapped in `<user_content>` tags
- System prompts explicitly instruct the model to treat tagged content as data, not instructions
- Never interpolate raw user input directly into system prompts
- The sanitizer in `core/security.py` checks for common injection patterns but does not block them outright (legitimate CVs might trigger false positives). Instead, it logs suspicious inputs for monitoring

### Rate Limiting
- Active on all POST endpoints from day one
- Configured in `core/rate_limiter.py` using slowapi
- Returns 429 with Retry-After header when exceeded
- Different limits per endpoint based on cost (LLM-heavy endpoints get stricter limits)
- Tracker endpoints rate limit per user (from JWT), not per IP

### Authentication and Authorization
- Supabase handles auth (signup, login, sessions, token refresh)
- Frontend sends the Supabase JWT in the Authorization header for protected endpoints
- Backend verifies the JWT on every protected request, extracts user_id
- Protected endpoints: all /api/tracker/*, POST /api/cv/parse, POST /api/cv/optimize, POST /api/cv/match
- Public endpoints: /api/query, /api/listings, /api/analytics/*, /api/health
- Admin endpoint: /api/ingest (uses X-Admin-Key, not user auth)
- Row Level Security on the applications table ensures data isolation at the database level

### API Security
- CORS allows only the frontend origin. Never `allow_origins=["*"]` in production
- Security headers set via middleware (X-Content-Type-Options, X-Frame-Options, CSP)
- Error responses never leak stack traces, file paths, or library versions
- CVs are processed in memory only. Never persisted to disk or Supabase

### Frontend Security
- All content rendered from API responses is sanitized with DOMPurify
- Client-side validation mirrors server-side but is not relied upon
- No secrets or API keys in frontend code except the Supabase anon key (which is designed to be public)
- The supabase.js file must contain a comment confirming it only uses the anon key

### Docker
- Both containers run as non-root users
- Only necessary ports are exposed
- Use specific image tags, not :latest

### Dependencies
- Pin all Python packages to exact versions in requirements.txt
- Commit package-lock.json for the frontend
- Do not install packages you do not need

## Coding Conventions

### Python (Backend)
- Use type hints on all function signatures
- Pydantic models for all request/response schemas
- Async endpoints where possible (FastAPI supports this natively)
- Docstrings on all service functions (Google style)
- Group imports: stdlib, third-party, local
- Use `logging` module, not print statements
- Handle errors with proper HTTP status codes and clear error messages
- No bare `except:` blocks. Always catch specific exceptions
- Security-sensitive operations (file handling, LLM calls, input processing) always wrapped in try/except with safe error messages returned to the client

### JavaScript/React (Frontend)
- Functional components with hooks only. No class components
- Custom hooks for shared logic (useChat, useOptimizer, useTracker, useAuth)
- Keep components focused: if a component file exceeds 150 lines, split it
- TailwindCSS utility classes for styling. No separate CSS files unless absolutely necessary
- Use fetch for API calls (no axios). Keep it simple
- The API client in `services/api.js` must automatically attach the auth token from the Supabase session to every request to protected endpoints
- PropTypes or JSDoc for component props. TypeScript is optional but not required
- Handle API errors gracefully in the UI. Show user-friendly messages, never raw error objects

### General
- No commented-out code in commits
- README stays up to date with any architecture changes
- Environment variables for all config. Never hardcode API keys or ports
- Meaningful variable names. No single-letter variables except loop counters

## Critical Constraints

### CV Optimizer Rules
- **NEVER invent or fabricate experience**. The optimizer only reframes, rewords, and reprioritizes what already exists on the CV
- **NEVER inflate skills**. If the user knows "basic Python", do not rewrite it as "proficient in Python"
- **Always explain why** a suggestion is made. Every rewrite comes with reasoning
- **Preserve technical accuracy**. Do not change the meaning of what someone built or did

### Data Rules
- Seed data must be synthetic. Do not copy real job postings from any website
- Job listings should be realistic and varied (different lengths, languages, styles)
- ChromaDB data must persist across restarts. Always use the persist directory
- Uploaded CVs are processed in memory and not persisted anywhere
- Application tracker data lives in Supabase, scoped to individual users via RLS

### Data Separation
- **ChromaDB**: job listings, embeddings, skill metadata. Shared across all users. No auth required to read
- **Supabase**: user accounts, application tracker entries. Per-user data, protected by auth and RLS
- These two data stores are independent. Do not try to sync them or create foreign key relationships between them. The `listing_id` field in the applications table is a soft reference (UUID stored as text), not a database-level foreign key

## Build Order
Always build in this order. Do not skip phases:
1. **Phase 0** ✅ DONE: Project scaffolding, .gitignore, .env setup, security foundation (config, sanitizer, rate limiter, CORS, middleware, Dockerfiles), Supabase project setup, migration, auth context
2. **Phase 1** ⬅ NEXT: Backend ingestion + RAG query + basic chat UI (get the core loop working first)
3. **Phase 2**: Skill extraction + analytics dashboard
4. **Phase 3**: CV parser + skill gap analysis + bullet rewriter + optimizer UI
5. **Phase 4**: Application tracker (CRUD, kanban board, stats, auth UI)

Within each phase, backend first, then frontend.

## Progress Log

### Phase 0 — Scaffolding & Security Foundation (complete)
Built and verified the full security baseline. Code-only steps done; steps needing
a live Supabase project are flagged below as pending manual setup.

- **Backend** (`backend/`):
  - `core/config.py` — `pydantic-settings` loader; secrets are `SecretStr` (opaque in logs); `VITE_` vars ignored; `cors_origins` parsed from comma-separated `ALLOWED_ORIGINS`
  - `core/security.py` — length-bounded sanitization, prompt-injection detection (logs, never blocks), `<user_content>` fencing that neutralizes delimiter-forgery, 3-way PDF validation (ext + MIME + magic bytes + 5MB)
  - `core/rate_limiter.py` — slowapi limiter, per-user-or-IP keying, friendly 429 + `Retry-After`
  - `core/supabase_client.py` — service-role admin client, server-side only
  - `core/auth.py` — JWT verified via Supabase `/auth/v1/user` (no JWT-secret management); stashes `user_id` for per-user rate limits
  - `api/dependencies.py` (`verify_admin_key`, constant-time compare), `api/middleware.py` (security headers + early 413 body cap), `api/routes/health.py`, `models/schemas.py`
  - `main.py` — CORS (never `*`), middleware wiring, exception handlers returning safe envelopes (no stack traces), `GET /api/health`
  - `requirements.txt` (pinned, targets Docker `python:3.11-slim`), non-root `Dockerfile`, `.dockerignore`
- **Frontend** (`frontend/`): anon-key-only `services/supabase.js`, `context/AuthContext.jsx` + `hooks/useAuth.js`, token-attaching `services/api.js`, Vite (reads `VITE_` vars from root `.env` via `envDir`), Tailwind (dark default), Phase-0 `App.jsx` shell (health ping + auth state), non-root `Dockerfile`
- **Infra**: `supabase/migrations/001_create_applications.sql` (RLS policies + `updated_at` trigger), `docker-compose.yml` (secrets only via `.env`), `Makefile`
- **Verified** via TestClient: health 200; security headers present; CORS allows only configured origin; oversized body → 413; unknown route → safe 404 envelope; `SecretStr` opaque; injection flagged; PDF magic-byte rejection; delimiter neutralization.

**Still pending (manual, requires external accounts):**
- Create the Supabase project, run `001_create_applications.sql`, fill real values into `.env`
- `frontend/package-lock.json` not yet generated (no `npm install` run); Dockerfile falls back to `npm install` if absent
- Local backend run needs Python 3.11–3.13 or Docker — the dev machine's Python 3.14 cannot build the pinned `pydantic==2.10.4` (PyO3 caps at 3.13)

## Common Pitfalls to Avoid
- Do not try to build a scraper. Use seed data. Scraping adds complexity and legal risk
- Do not over-engineer the LLM prompts. Start simple, iterate based on output quality
- Do not use LangChain for everything. Use it for the RAG chain, but write custom code for skill extraction and CV parsing if it is simpler
- Do not make the frontend pixel-perfect before the backend works. Get the data flowing first
- ChromaDB can be finicky with metadata filtering. Test filters early
- The bullet rewriter makes multiple LLM calls. Add basic rate limiting or queuing so it does not hammer the API
- Do not skip Phase 0. Security scaffolding must exist before any feature code
- Do not catch exceptions silently. Log them server-side, return safe messages client-side
- Do not create a VITE_SUPABASE_SERVICE_ROLE_KEY variable. Ever. For any reason
- Do not store CVs in Supabase or on disk. Process in memory only
- Do not create database-level foreign keys between Supabase and ChromaDB. Use soft references

## File Naming
- Backend: snake_case for everything (files, functions, variables)
- Frontend: PascalCase for components (ChatInterface.jsx), camelCase for hooks and utilities (useChat.js, api.js)
- No spaces in filenames anywhere

## Testing Notes
- Backend: test the RAG pipeline with a few known listings and expected queries
- Test the CV parser with at least 3 different CV formats (different section orderings, languages)
- Test the skill extractor with listings that use different terminology for the same skill (e.g., "JS" vs "JavaScript" vs "ES6")
- Test input validation: send oversized payloads, invalid file types, and strings with injection patterns to verify they are handled correctly
- Test rate limiting: verify that exceeding the limit returns 429 with a Retry-After header
- Test auth: verify that unauthenticated requests to protected endpoints return 401
- Test RLS: verify that a user cannot access another user's application tracker entries (try with a direct Supabase query using a different user's token)
- Test that the service role key does not appear in any frontend bundle (build the frontend and search the output files)
- Frontend: manual testing is fine for a portfolio project. No need for a test framework unless things get complex

## Deployment Target
- For now: runs locally with Docker Compose (backend + frontend + ChromaDB) plus hosted Supabase
- Future: deploy to Railway, Render, or Hugging Face Spaces
- The app should work with `docker-compose up` plus a configured Supabase project
