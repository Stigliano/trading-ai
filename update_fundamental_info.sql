-- Ricreiamo la tabella fundamental_info con una struttura più semplice
DROP TABLE IF EXISTS fundamental_info;

CREATE TABLE fundamental_info (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_fundinfo_symbol ON fundamental_info(symbol);
CREATE INDEX idx_fundinfo_key ON fundamental_info(key);
