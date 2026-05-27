-- DeployMe — applications table for the job application tracker.
-- Run this in the Supabase SQL editor (or via the Supabase CLI) once per project.
--
-- Row Level Security is the last line of defense for per-user data isolation:
-- even if the backend has a bug, Postgres itself will not return another user's
-- rows. The service role key bypasses RLS, so it is never used to serve
-- user-scoped reads/writes — those go through the user's own JWT.

CREATE TABLE IF NOT EXISTS applications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  company VARCHAR(200) NOT NULL,
  role VARCHAR(200) NOT NULL,
  location VARCHAR(200),
  status VARCHAR(20) NOT NULL DEFAULT 'saved'
    CHECK (status IN ('saved', 'applied', 'interviewing', 'offer', 'rejected', 'ghosted')),
  applied_date DATE,
  listing_id UUID,              -- optional soft link to a ChromaDB listing (NOT a FK)
  listing_url TEXT,             -- original job posting URL
  notes TEXT,                   -- max 2000 chars enforced at the API level
  next_step TEXT,               -- e.g. "Technical interview on June 5"
  cv_version TEXT,              -- which CV version was used
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Row Level Security: a user can only touch their own rows ───────────────
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own applications"
  ON applications FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own applications"
  ON applications FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own applications"
  ON applications FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own applications"
  ON applications FOR DELETE
  USING (auth.uid() = user_id);

-- ─── Indexes for fast per-user lookups ──────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(user_id, status);

-- ─── Keep updated_at fresh on every UPDATE ──────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS applications_set_updated_at ON applications;
CREATE TRIGGER applications_set_updated_at
  BEFORE UPDATE ON applications
  FOR EACH ROW
  EXECUTE FUNCTION set_updated_at();
