-- Mirrors app.models.market_data.Quote.
CREATE TABLE quotes (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES simulation_sessions (id) ON DELETE CASCADE,
    symbol VARCHAR(5) NOT NULL REFERENCES stocks (symbol) ON DELETE CASCADE,
    "timestamp" TIMESTAMPTZ NOT NULL,
    bid NUMERIC(18, 6) NOT NULL CHECK (bid > 0),
    ask NUMERIC(18, 6) NOT NULL CHECK (ask > 0),
    bid_size INTEGER NOT NULL CHECK (bid_size > 0),
    ask_size INTEGER NOT NULL CHECK (ask_size > 0),
    CONSTRAINT quotes_bid_lower_than_ask CHECK (bid < ask)
);
