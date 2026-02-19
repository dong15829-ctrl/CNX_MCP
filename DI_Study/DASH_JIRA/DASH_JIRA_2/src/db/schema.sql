-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Issues Table
CREATE TABLE IF NOT EXISTS issues (
    issue_key VARCHAR(50) PRIMARY KEY,
    issue_id BIGINT,
    summary TEXT,
    description TEXT,
    status VARCHAR(50),
    issue_type VARCHAR(50),
    priority VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    assignee_id VARCHAR(100),
    reporter_id VARCHAR(100),
    custom_fields JSONB DEFAULT '{}'::jsonb,
    analysis_result JSONB DEFAULT '{}'::jsonb
);

-- Comments Table
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    issue_key VARCHAR(50) REFERENCES issues(issue_key) ON DELETE CASCADE,
    author_id VARCHAR(100),
    body TEXT,
    created_at TIMESTAMP,
    is_internal BOOLEAN DEFAULT FALSE
);

-- Embeddings Table
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    issue_key VARCHAR(50) REFERENCES issues(issue_key) ON DELETE CASCADE,
    embedding_type VARCHAR(20), -- 'summary', 'full_context', 'resolution'
    vector VECTOR(1536),
    model_version VARCHAR(50)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_assignee ON issues(assignee_id);
CREATE INDEX IF NOT EXISTS idx_comments_issue_key ON comments(issue_key);
