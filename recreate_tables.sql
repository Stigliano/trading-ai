-- Drop tabelle esistenti se necessario
DROP TABLE IF EXISTS stock_daily_prices;
DROP TABLE IF EXISTS intraday_data;
DROP TABLE IF EXISTS fundamental_info;
DROP TABLE IF EXISTS fundamental_financials;
DROP TABLE IF EXISTS fundamental_balance;
DROP TABLE IF EXISTS fundamental_cashflow;
DROP TABLE IF EXISTS macroeconomic_data;
DROP TABLE IF EXISTS news_sentiment;
DROP TABLE IF EXISTS sector_performance;

-- Crea tabella per dati di mercato giornalieri
CREATE TABLE stock_daily_prices (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    symbol VARCHAR(20),
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT idx_stock_daily_prices_date_symbol UNIQUE (date, symbol)
);

-- Crea indici per prestazioni
CREATE INDEX idx_stock_date ON stock_daily_prices(date);
CREATE INDEX idx_stock_symbol ON stock_daily_prices(symbol);

-- Tabella per i dati intraday
CREATE TABLE intraday_data (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP,
    symbol VARCHAR(20),
    interval VARCHAR(10),
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT idx_intraday_datetime_symbol_interval UNIQUE (datetime, symbol, interval)
);

-- Crea indici per prestazioni
CREATE INDEX idx_intraday_datetime ON intraday_data(datetime);
CREATE INDEX idx_intraday_symbol ON intraday_data(symbol);

-- Tabella per i dati fondamentali info
CREATE TABLE fundamental_info (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    key VARCHAR(100),
    value TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_fundinfo_symbol ON fundamental_info(symbol);
CREATE INDEX idx_fundinfo_key ON fundamental_info(key);

-- Tabella per i dati fondamentali financials
CREATE TABLE fundamental_financials (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    date TIMESTAMP,
    metric VARCHAR(100),
    value FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_financials_symbol_date ON fundamental_financials(symbol, date);

-- Tabella per i dati fondamentali balance sheet
CREATE TABLE fundamental_balance (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    date TIMESTAMP,
    metric VARCHAR(100),
    value FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_balance_symbol_date ON fundamental_balance(symbol, date);

-- Tabella per i dati fondamentali cashflow
CREATE TABLE fundamental_cashflow (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    date TIMESTAMP,
    metric VARCHAR(100),
    value FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cashflow_symbol_date ON fundamental_cashflow(symbol, date);

-- Tabella per i dati macroeconomici
CREATE TABLE macroeconomic_data (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    indicator VARCHAR(50),
    name VARCHAR(100),
    value FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_macro_date_indicator ON macroeconomic_data(date, indicator);

-- Tabella per notizie e sentiment
CREATE TABLE news_sentiment (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    symbol VARCHAR(20),
    title TEXT,
    sentiment FLOAT,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_news_date_symbol ON news_sentiment(date, symbol);

-- Tabella per performance settoriale
CREATE TABLE sector_performance (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    sector VARCHAR(50),
    etf VARCHAR(20),
    performance_1mo FLOAT,
    performance_3mo FLOAT,
    last_price FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sector_date ON sector_performance(date);
CREATE INDEX idx_sector_sector ON sector_performance(sector);
