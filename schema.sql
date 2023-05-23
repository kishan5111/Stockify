-- schema.sql

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    cash NUMERIC NOT NULL DEFAULT 10000.00
);

CREATE TABLE sqlite_sequence (name, seq);

CREATE UNIQUE INDEX username ON users (username);

CREATE TABLE stock_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    user_id INTEGER,
    purchase_date DATE,
    purchase_time TIME,
    purchase_price NUMERIC,
    shares NUMERIC,
    stock_name TEXT,
    total_price NUMERIC,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    user_id INTEGER,
    purchase_date DATE,
    purchase_time TIME,
    purchase_price NUMERIC,
    shares NUMERIC,
    stock_name TEXT,
    total_price NUMERIC,
    sale_price NUMERIC,
    sale_purchase TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
