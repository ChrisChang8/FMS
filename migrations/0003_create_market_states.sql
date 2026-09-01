-- Mirrors app.models.market_data.MarketState; current behavior snapshot per session/symbol.
CREATE TABLE market_states (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES simulation_sessions (id) ON DELETE CASCADE,
    symbol VARCHAR(5) NOT NULL REFERENCES stocks (symbol) ON DELETE CASCADE,
    trend TEXT NOT NULL CHECK (trend IN ('normal', 'uptrend', 'downtrend', 'sideways')),
    volatility NUMERIC(18, 6) NOT NULL CHECK (volatility >= 0),
    liquidity NUMERIC(5, 4) NOT NULL CHECK (liquidity BETWEEN 0 AND 1),
    momentum NUMERIC(5, 4) NOT NULL CHECK (momentum BETWEEN -1 AND 1),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT market_states_session_symbol_unique UNIQUE (session_id, symbol)
);
