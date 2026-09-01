-- Mirrors app.models.market_data.Candle.
CREATE TABLE candles (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES simulation_sessions (id) ON DELETE CASCADE,
    symbol VARCHAR(5) NOT NULL REFERENCES stocks (symbol) ON DELETE CASCADE,
    "interval" TEXT NOT NULL CHECK ("interval" ~ '^[1-9][0-9]*(s|m|h|d)$'),
    "timestamp" TIMESTAMPTZ NOT NULL,
    open NUMERIC(18, 6) NOT NULL CHECK (open > 0),
    high NUMERIC(18, 6) NOT NULL CHECK (high > 0),
    low NUMERIC(18, 6) NOT NULL CHECK (low > 0),
    close NUMERIC(18, 6) NOT NULL CHECK (close > 0),
    volume BIGINT NOT NULL CHECK (volume > 0),
    trade_count INTEGER NOT NULL CHECK (trade_count > 0),
    CONSTRAINT candles_low_lower_than_high CHECK (low <= high),
    CONSTRAINT candles_high_is_max CHECK (high = GREATEST(open, high, low, close)),
    CONSTRAINT candles_low_is_min CHECK (low = LEAST(open, high, low, close)),
    CONSTRAINT candles_session_symbol_interval_timestamp_unique UNIQUE (session_id, symbol, "interval", "timestamp")
);
