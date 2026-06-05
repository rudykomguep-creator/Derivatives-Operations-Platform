import sqlite3, os
from datetime import date, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "derivops.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS trades (
        trade_id TEXT PRIMARY KEY,
        product TEXT,
        counterparty TEXT,
        ticker TEXT,
        quantity REAL,
        price REAL,
        trade_date TEXT,
        settlement_date TEXT,
        status TEXT DEFAULT 'Pending',
        source TEXT DEFAULT 'Manual',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS trade_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id TEXT,
        event_type TEXT,
        description TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS breaks (
        break_id TEXT PRIMARY KEY,
        break_type TEXT,
        ticker TEXT,
        fo_value TEXT,
        bo_value TEXT,
        delta TEXT,
        severity TEXT,
        status TEXT DEFAULT 'Open',
        description TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS settlements (
        settlement_id TEXT PRIMARY KEY,
        trade_id TEXT,
        ticker TEXT,
        quantity REAL,
        amount REAL,
        due_date TEXT,
        cycle TEXT,
        status TEXT DEFAULT 'Pending'
    );

    CREATE TABLE IF NOT EXISTS journals (
        entry_id TEXT,
        trade_id TEXT,
        account TEXT,
        debit REAL DEFAULT 0,
        credit REAL DEFAULT 0,
        validated INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS incidents (
        ticket_id TEXT PRIMARY KEY,
        break_id TEXT,
        description TEXT,
        priority TEXT,
        analysis TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS lifecycle_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id TEXT,
        product TEXT,
        ticker TEXT,
        event_type TEXT,
        event_date TEXT,
        status TEXT DEFAULT 'Pending',
        notes TEXT
    );
    """)

    # Seed demo data if empty
    if c.execute("SELECT COUNT(*) FROM trades").fetchone()[0] == 0:
        _seed(c)

    conn.commit()
    conn.close()

def _seed(c):
    today = date.today()
    t2 = (today + timedelta(days=2)).isoformat()
    t3 = (today + timedelta(days=3)).isoformat()

    trades = [
        ("TRD-001", "Equity Option", "Alpha Capital", "AAPL", 500, 194.20, today.isoformat(), t2, "Affirmed", "FO"),
        ("TRD-002", "Equity Future", "Vertex Fund", "ES", 10, 5234.50, today.isoformat(), t2, "Pending", "FO"),
        ("TRD-003", "Equity Swap", "Nexus Securities", "MSFT", 1000, 412.80, today.isoformat(), t2, "Break", "FO"),
        ("TRD-004", "Equity", "Meridian Prime", "NVDA", 200, 887.30, today.isoformat(), t2, "Settled", "FO"),
        ("TRD-005", "Bond", "Atlas Partners", "US10Y", 50, 98.40, today.isoformat(), t3, "Pending", "FO"),
        ("TRD-006", "Equity", "Quantum AM", "SPY", 300, 523.10, today.isoformat(), t2, "Affirmed", "FO"),
        ("TRD-007", "Equity Option", "Citrine Trading", "NVDA", 200, 887.30, today.isoformat(), t2, "Break", "FO"),
        ("TRD-008", "Equity", "Pinnacle Global", "GOOG", 150, 1769.00, today.isoformat(), t3, "Pending", "FO"),
    ]
    c.executemany("INSERT OR IGNORE INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))", trades)

    breaks = [
        ("BRK-001", "Position break", "AAPL", "500", "450", "-50", "High", "Open", "FO=500 shares, BO=450 shares. Likely partial booking."),
        ("BRK-002", "Price mismatch", "NVDA", "887.30", "884.00", "-3.30", "Medium", "In Review", "Price discrepancy between FO and BO booking."),
        ("BRK-003", "Cash break", "MSFT", "412800.00", "0.00", "-412800.00", "High", "Open", "Expected cash not received. Settlement failed."),
        ("BRK-004", "Missing trade", "SPY", "Present", "Not found", "—", "Low", "Resolved", "BO trade not in FO — duplicate removed."),
    ]
    c.executemany("INSERT OR IGNORE INTO breaks VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))", breaks)

    settlements = [
        ("STL-001", "TRD-001", "AAPL", 500, 97100.00, t2, "T+2", "Settled"),
        ("STL-002", "TRD-003", "MSFT", 1000, 412800.00, t2, "T+2", "Failed"),
        ("STL-003", "TRD-004", "NVDA", 200, 177460.00, t2, "T+2", "Settled"),
        ("STL-004", "TRD-008", "GOOG", 150, 265350.00, t3, "T+3", "Pending"),
        ("STL-005", "TRD-006", "SPY", 300, 156930.00, t2, "T+2", "Settled"),
        ("STL-006", "TRD-002", "ES", 10, 52345.00, t2, "T+2", "Pending"),
    ]
    c.executemany("INSERT OR IGNORE INTO settlements VALUES (?,?,?,?,?,?,?,?)", settlements)

    journals = [
        ("JNL-001", "TRD-001", "Equity Position", 97100, 0, 1),
        ("JNL-001", "TRD-001", "Cash", 0, 97100, 1),
        ("JNL-002", "TRD-004", "Equity Position", 177460, 0, 1),
        ("JNL-002", "TRD-004", "Cash", 0, 177460, 1),
        ("JNL-003", "TRD-003", "Equity Position", 412800, 0, 0),
    ]
    c.executemany("INSERT OR IGNORE INTO journals (entry_id,trade_id,account,debit,credit,validated) VALUES (?,?,?,?,?,?)", journals)

    incidents = [
        ("INC-042", "BRK-001", "Position break AAPL +50 — partial booking", "High", "Probable partial booking at BO level."),
        ("INC-043", "BRK-003", "Cash break MSFT TRS — payment not received", "High", "Settlement instruction mismatch."),
    ]
    c.executemany("INSERT OR IGNORE INTO incidents VALUES (?,?,?,?,?,datetime('now'))", incidents)

    lifecycle = [
        ("TRD-001", "Equity Option", "AAPL", "Open", "2026-05-01", "Done", "500 contracts @ $3.40"),
        ("TRD-001", "Equity Option", "AAPL", "Expiration", "2026-06-20", "Upcoming", "15 days remaining"),
        ("TRD-003", "Equity Swap", "MSFT", "Effective Date", "2026-05-01", "Done", "TRS initiated"),
        ("TRD-003", "Equity Swap", "MSFT", "Reset Date", "2026-06-01", "Done", "Reset applied"),
        ("TRD-003", "Equity Swap", "MSFT", "Payment Date", "2026-06-07", "Upcoming", "2 days"),
        ("TRD-003", "Equity Swap", "MSFT", "Maturity", "2026-11-01", "Pending", ""),
        ("TRD-002", "Equity Future", "ES", "Open", "2026-05-15", "Done", "10 contracts"),
        ("TRD-002", "Equity Future", "ES", "Maturity", "2026-09-19", "Pending", "Quarterly expiry"),
    ]
    c.executemany("INSERT OR IGNORE INTO lifecycle_events (trade_id,product,ticker,event_type,event_date,status,notes) VALUES (?,?,?,?,?,?,?)", lifecycle)
