-- Mirrors app.simulation.behaviors.MarketBehaviorConfig/BehaviorType; append-only history log.
CREATE TABLE market_behaviors (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES simulation_sessions (id) ON DELETE CASCADE,
    symbol VARCHAR(5) NOT NULL REFERENCES stocks (symbol) ON DELETE CASCADE,
    behavior_type TEXT NOT NULL CHECK (
        behavior_type IN (
            'normal',
            'uptrend',
            'downtrend',
            'sideways',
            'momentum',
            'mean_reversion',
            'breakout',
            'breakdown',
            'consolidation',
            'volatility_spike'
        )
    ),
    start_time TIMESTAMPTZ NOT NULL,
    duration_seconds NUMERIC NOT NULL CHECK (duration_seconds > 0),
    strength NUMERIC(5, 4) NOT NULL CHECK (strength BETWEEN -1 AND 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
