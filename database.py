import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "etally.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            password TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vessels (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            voyage TEXT NOT NULL,
            berth_no TEXT NOT NULL,
            arrival_date TEXT NOT NULL,
            total_units INTEGER DEFAULT 0,
            status TEXT DEFAULT 'BERTHED'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chassis (
            vin TEXT PRIMARY KEY,
            last_6 TEXT NOT NULL,
            vessel_id TEXT NOT NULL,
            model TEXT NOT NULL,
            brand_new_used TEXT DEFAULT 'USED',
            iid TEXT,
            color TEXT,
            deck TEXT,
            yard TEXT,
            row_lane TEXT,
            tally_status TEXT DEFAULT 'No Tally',
            FOREIGN KEY (vessel_id) REFERENCES vessels(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tally_sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vin TEXT UNIQUE NOT NULL,
            doc_ref TEXT NOT NULL,
            vessel_id TEXT NOT NULL,
            tally_type TEXT DEFAULT 'ONBOARD',
            status TEXT DEFAULT 'Draft',
            accessories_json TEXT,
            damages_json TEXT,
            photos_json TEXT,
            remarks TEXT,
            created_by TEXT,
            created_at TEXT,
            confirmed_by TEXT,
            confirmed_at TEXT,
            FOREIGN KEY (vin) REFERENCES chassis(vin)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS update_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vin TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'PENDING',
            approved_by TEXT,
            updated_at TEXT,
            FOREIGN KEY (vin) REFERENCES chassis(vin)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vin TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL,
            discrepancies_json TEXT,
            remarks TEXT,
            checked_by TEXT,
            checked_at TEXT,
            FOREIGN KEY (vin) REFERENCES chassis(vin)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vin TEXT NOT NULL,
            work_point TEXT NOT NULL,
            user_id TEXT NOT NULL,
            user_role TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            details TEXT
        )
    """)

    conn.commit()
    seed_data(conn)
    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Seed Users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        users = [
            ('admin', 'System Administrator', 'Admin', 'admin123', 'ACTIVE', now_str),
            ('surveyor298', 'Surveyor 298', 'Surveyor', 'pass123', 'ACTIVE', now_str),
            ('supervisor352', 'Supervisor 352', 'Supervisor', 'pass123', 'ACTIVE', now_str),
            ('security5958', 'Security Officer 5958', 'Security', 'pass123', 'ACTIVE', now_str),
            ('driver60664', 'Driver 60664', 'Driver', 'pass123', 'ACTIVE', now_str),
        ]
        cursor.executemany("INSERT INTO users (username, name, role, password, status, created_at) VALUES (?,?,?,?,?,?)", users)

    # Seed Vessels
    cursor.execute("SELECT COUNT(*) FROM vessels")
    if cursor.fetchone()[0] == 0:
        now = datetime.now()
        date_str = now.strftime("%Y/%m/%d")
        vessels = [
            ('VSL001', 'VIKING DRIVE', '41', 'Berth 1', date_str, 120, 'BERTHED'),
            ('VSL002', 'HOEGH STRIKER', '108', 'Berth 2', date_str, 85, 'BERTHED'),
            ('VSL003', 'EUKOR HORIZON', '65', 'Berth 3', date_str, 200, 'BERTHED'),
        ]
        cursor.executemany("INSERT INTO vessels VALUES (?,?,?,?,?,?,?)", vessels)

        chassis_list = [
            ('RV5-1268273', '268273', 'VSL001', 'VEZEL', 'USED', 'ROV#4953-01022', 'Pearl White', 'Deck 3', 'Yard A', 'Block 2-Row 4', 'Confirmed'),
            ('KDH2010143285', '143285', 'VSL001', 'KDH HIACE', 'USED', 'ROV#4953-01023', 'Silver', 'Deck 2', 'Yard B', 'Block 1-Row 2', 'Confirmed'),
            ('ZVW30-5849102', '849102', 'VSL001', 'PRIUS', 'USED', 'ROV#4953-01024', 'Black', 'Deck 4', 'Yard A', 'Block 3-Row 1', 'No Tally'),
            ('NKE165-3819204', '819204', 'VSL001', 'AXIO', 'BRAND NEW', 'ROV#4953-01025', 'Wine Red', 'Deck 1', 'Yard C', 'Block 4-Row 5', 'No Tally'),
            ('DA64V-7718293', '718293', 'VSL002', 'EVERY', 'USED', 'ROV#4953-01026', 'White', 'Deck 2', 'Yard B', 'Block 2-Row 1', 'No Tally'),
            ('MXAA54-0091823', '091823', 'VSL002', 'RAV4', 'BRAND NEW', 'ROV#4953-01027', 'Blue', 'Deck 3', 'Yard A', 'Block 1-Row 3', 'No Tally'),
            ('FK7-1002938', '002938', 'VSL003', 'CIVIC HATCHBACK', 'USED', 'ROV#4953-01028', 'Sonic Gray', 'Deck 5', 'Yard C', 'Block 5-Row 2', 'No Tally'),
        ]
        cursor.executemany("INSERT INTO chassis VALUES (?,?,?,?,?,?,?,?,?,?,?)", chassis_list)

    conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
