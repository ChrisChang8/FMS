-- Mirrors app.models.market_data.MarketTick.
CREATE TABLE market_ticks (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES simulation_sessions (id) ON DELETE CASCADE,
    symbol VARCHAR(5) NOT NULL REFERENCES stocks (symbol) ON DELETE CASCADE,
    "timestamp" TIMESTAMPTZ NOT NULL,
    price NUMERIC(18, 6) NOT NULL CHECK (price > 0),
    bid NUMERIC(18, 6) NOT NULL CHECK (bid > 0),
    ask NUMERIC(18, 6) NOT NULL CHECK (ask > 0),
    bid_size INTEGER NOT NULL CHECK (bid_size > 0),
    ask_size INTEGER NOT NULL CHECK (ask_size > 0),
    trade_volume INTEGER NOT NULL CHECK (trade_volume > 0),
    sequence_number BIGINT NOT NULL CHECK (sequence_number > 0),
    CONSTRAINT market_ticks_bid_lower_than_ask CHECK (bid < ask),
    CONSTRAINT market_ticks_price_within_spread CHECK (price BETWEEN bid AND ask),
    CONSTRAINT market_ticks_session_symbol_sequence_unique UNIQUE (session_id, symbol, sequence_number)
);
