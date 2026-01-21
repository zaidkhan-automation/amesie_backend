CREATE TABLE IF NOT EXISTS user_facts (
    fact_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    fact_key TEXT NOT NULL,
    fact_value TEXT NOT NULL,

    r_raw FLOAT DEFAULT 0.0,
    p_raw FLOAT DEFAULT 0.0,

    source TEXT DEFAULT 'llm_extraction',
    active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    last_confirmed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_facts_user ON user_facts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_facts_key ON user_facts(user_id, fact_key);
