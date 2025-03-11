-- Ricreiamo la tabella sector_performance con una struttura corretta
DROP TABLE IF EXISTS sector_performance;

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
