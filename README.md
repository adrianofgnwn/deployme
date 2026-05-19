# 🚀 DeployMe

**Deploy yourself into the job market.**

DeployMe is a RAG-powered web application that helps tech job seekers analyze the job market, optimize their CVs for specific roles, and track their application pipeline — all in one place.

Built for CS students and junior developers applying for internships and entry-level positions in the German tech market.

<!-- TODO: Add a screenshot or GIF of the app here once the UI is ready -->
<!-- ![DeployMe Screenshot](./docs/screenshot.png) -->

---

## What It Does

**Job Market Chat** — Ask natural language questions about tech job listings and get grounded answers citing specific postings. "Which companies in NRW are hiring ML interns?" or "What skills appear most in backend developer roles?"

**Skill Analytics** — See which skills are most in demand across listings, filter by location and role type, and spot trends in what employers are looking for.

**CV Optimizer** — Upload your CV, pick a job listing, and get actionable suggestions. The optimizer identifies skill gaps, rewrites bullet points to better match the role's language, and tells you which projects to emphasize — without ever inventing or inflating your experience.

**Application Tracker** — Log your applications, track their status through a kanban board, add interview notes, and see pipeline analytics like response rates and weekly trends. Connects directly to the optimizer so you can go from "optimize CV" to "track this application" in one click.

---

## Tech Stack

### Backend
- Python, FastAPI
- LangChain, sentence-transformers (`all-MiniLM-L6-v2`), ChromaDB
- Anthropic API (Claude) for LLM-powered features
- Supabase (PostgreSQL) for auth and application tracker data

### Frontend
- React, Vite, TailwindCSS
- Recharts for data visualizations
- Supabase client for authentication

### Infrastructure
- Docker Compose
- Row Level Security (RLS) for per-user data isolation

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│          React + Vite + TailwindCSS              │
│                                                  │
│  ┌──────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐ │
│  │ Chat │ │Analytics │ │Optimizer│ │ Tracker │  │
│  └──┬───┘ └────┬─────┘ └────┬────┘ └────┬────┘ │
└─────┼──────────┼────────────┼───────────┼───────┘
      │          │            │           │
      ▼          ▼            ▼           ▼
┌─────────────────────────────────────────────────┐
│                   Backend                        │
│                   FastAPI                         │
│                                                  │
│  ┌────────────┐ ┌──────────┐ ┌───────────────┐  │
│  │RAG Pipeline│ │CV Parser │ │Tracker Service│  │
│  │ + LLM      │ │+ Rewriter│ │               │  │
│  └─────┬──────┘ └────┬─────┘ └───────┬───────┘  │
└────────┼─────────────┼───────────────┼──────────┘
         │             │               │
         ▼             ▼               ▼
   ┌──────────┐  ┌──────────┐   ┌──────────┐
   │ ChromaDB │  │Anthropic │   │ Supabase │
   │ (vectors)│  │   API    │   │(auth+db) │
   └──────────┘  └──────────┘   └──────────┘
```

**Data separation:** ChromaDB stores job listings and embeddings (shared, public). Supabase stores user accounts and application tracker entries (per-user, protected by RLS). The two stores are independent.

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- A Supabase project (free tier works fine)
- An Anthropic API key

### 1. Clone the repo

```bash
git clone https://github.com/adrianofgnwn/deployme.git
cd deployme
```

### 2. Set up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to the SQL Editor and run the migration in `supabase/migrations/001_create_applications.sql`
3. Copy your project URL, anon key, and service role key from Settings > API

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
ANTHROPIC_API_KEY=your-anthropic-key
ADMIN_API_KEY=pick-a-strong-admin-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

> ⚠️ Never commit the `.env` file. It's in `.gitignore` by default.

### 4. Run the app

```bash
docker-compose up
```

The app will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

Seed data loads automatically on first startup.

---

## Features in Detail

### Job Market Chat
Ask questions in natural language. The RAG pipeline retrieves relevant job listings from ChromaDB and generates grounded answers with citations.

<!-- TODO: Add screenshot -->

### Skill Analytics
Interactive dashboard showing skill demand across all listings. Filter by location, role type, and experience level. See which skills are trending up.

<!-- TODO: Add screenshot -->

### CV Optimizer
Upload your CV (PDF or paste text), select a target job listing, and get:
- **Skill gap analysis** — what you have, what you're missing, and bonus matches
- **Bullet point rewrites** — side-by-side suggestions with explanations for each change
- **General tips** — section ordering, skill categorization, what to emphasize

The optimizer never invents experience. It only reframes what's already on your CV.

<!-- TODO: Add screenshot -->

### Application Tracker
Track every application from saved to offer (or rejected). Features:
- Kanban board with drag-and-drop status updates
- Sortable list view with filters
- Interview notes and next steps
- Pipeline analytics (response rate, weekly trends, status breakdown)

Requires a free account (email signup or magic link).

<!-- TODO: Add screenshot -->

---

## Security

This project was built with security as a first-class concern:

- **Input validation**: all inputs validated with Pydantic, file uploads checked three ways (MIME, extension, magic bytes)
- **Prompt injection defense**: user content wrapped in delimiters, system prompts explicitly instruct the LLM to treat user content as data
- **Rate limiting**: all mutation endpoints rate-limited with slowapi, stricter limits on LLM-heavy endpoints
- **Authentication**: Supabase handles user auth with JWT verification on every protected request
- **Data isolation**: Row Level Security (RLS) on the applications table ensures users can only access their own data
- **Secrets management**: all keys in `.env` (gitignored), service role key never exposed to the frontend
- **CORS**: configured to allow only the frontend origin
- **Docker**: containers run as non-root users

---

## Project Structure

```
deployme/
├── backend/            # FastAPI backend
│   ├── api/            # Route handlers
│   ├── core/           # Config, security, auth, RAG pipeline
│   ├── services/       # Business logic
│   ├── models/         # Pydantic schemas
│   └── data/           # Seed data
├── frontend/           # React frontend
│   ├── src/
│   │   ├── pages/      # Page components
│   │   ├── components/ # Reusable UI components
│   │   ├── hooks/      # Custom React hooks
│   │   ├── context/    # Auth context
│   │   └── services/   # API client, Supabase client
├── supabase/           # Database migrations
└── docker-compose.yml
```

---

## Available Commands

```bash
make dev          # Start development servers
make seed         # Load seed data into ChromaDB
make reset-db     # Reset ChromaDB data
make docker-up    # Start everything with Docker Compose
```

---

## Built By

**Adriano Ferane Gunawan**
B.Sc. Computer Science Student, FH Aachen

- [LinkedIn](https://www.linkedin.com/in/adrianofgunawan/)
- [GitHub](https://github.com/adrianofgnwn)

---

## License

<!-- TODO: Choose a license. MIT is standard for portfolio projects -->
MIT License
