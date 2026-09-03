-- Mirrors app.models.market_data.Stock.
CREATE TABLE stocks (
    symbol VARCHAR(5) PRIMARY KEY,
    company_name TEXT NOT NULL,
    starting_price NUMERIC(18, 6) NOT NULL CHECK (starting_price > 0),
    sector TEXT NOT NULL,
    average_volume BIGINT NOT NULL CHECK (average_volume > 0),
    base_volatility NUMERIC(18, 6) NOT NULL CHECK (base_volatility >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT stocks_symbol_uppercase CHECK (symbol = UPPER(symbol))
);
