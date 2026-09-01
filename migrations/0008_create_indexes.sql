-- Supports time-range lookups and replay per session/symbol.
CREATE INDEX idx_quotes_session_symbol_timestamp ON quotes (session_id, symbol, "timestamp");
CREATE INDEX idx_market_ticks_session_symbol_timestamp ON market_ticks (session_id, symbol, "timestamp");
CREATE INDEX idx_candles_session_symbol_interval_timestamp ON candles (session_id, symbol, "interval", "timestamp");
CREATE INDEX idx_market_behaviors_session_symbol_start_time ON market_behaviors (session_id, symbol, start_time);
