-- Groups ticks, quotes, candles, and behaviors under one reproducible simulation run.
CREATE TABLE simulation_sessions (
    id BIGSERIAL PRIMARY KEY,
    seed INTEGER NOT NULL,
    drift DOUBLE PRECISION NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT simulation_sessions_ended_after_started CHECK (ended_at IS NULL OR ended_at >= started_at)
);
