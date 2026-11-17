"""
database.py
Simple SQLite database helper for Credit Default Risk Prediction System.
Handles customer records, whitelist entries, and customer risk alerts.
"""

import sqlite3
import os
import json
from datetime import datetime

# Path to the SQLite database file
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "credit_system.db")


def get_connection():
    """Returns a SQLite connection with row dictionary access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables in the SQLite database."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: Evaluated Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            probability REAL NOT NULL,
            prediction TEXT NOT NULL,
            risk_category TEXT NOT NULL,
            review_status TEXT DEFAULT 'Not Reviewed',
            limit_bal REAL,
            age INTEGER,
            pay_1 INTEGER,
            bill_amt1 REAL,
            pay_amt1 REAL,
            top_reasons TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Table 2: Whitelisted Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            reason TEXT NOT NULL,
            notes TEXT,
            added_at TEXT NOT NULL
        )
    """)

    # Table 3: Customer Risk Alerts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            probability REAL NOT NULL,
            alert_date TEXT NOT NULL,
            alert_status TEXT DEFAULT 'Pending',
            message TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed demo records from actual dataset if table is currently empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_sample_records(conn)

    conn.close()


def seed_sample_records(conn):
    """Adds a few initial verified records so the user immediately sees working data."""
    cursor = conn.cursor()
    sample_customers = [
        ("CUST-1001", 78.4, "Default", "High Risk", "Not Reviewed", 20000, 24, 2, 3913, 0,
         json.dumps(["2-month payment delay on recent statement", "Low payment amount ($0) against bill", "Low overall credit limit ($20,000)"])),
        ("CUST-1002", 64.2, "Default", "High Risk", "Not Reviewed", 120000, 26, 2, 2682, 0,
         json.dumps(["Payment delay in current cycle", "Low monthly payment activity"])),
        ("CUST-1003", 18.5, "No Default", "Low Risk", "Reviewed", 90000, 34, 0, 29239, 1518,
         json.dumps(["Consistent revolving payments on time", "Healthy credit utilization"])),
        ("CUST-1004", 42.1, "No Default", "Moderate Risk", "Not Reviewed", 50000, 37, 0, 46990, 2000,
         json.dumps(["High bill amount near credit limit", "Pays minimum balance monthly"])),
        ("CUST-1005", 12.3, "No Default", "Low Risk", "Reviewed", 500000, 40, -1, 8617, 8617,
         json.dumps(["Paid statement balance in full", "High credit limit with excellent repayment score"]))
    ]

    for c in sample_customers:
        cursor.execute("""
            INSERT OR IGNORE INTO customers (
                customer_id, probability, prediction, risk_category, review_status,
                limit_bal, age, pay_1, bill_amt1, pay_amt1, top_reasons, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], datetime.now().strftime("%Y-%m-%d %H:%M")))

    # Seed 2 sample demo alerts
    cursor.execute("""
        INSERT INTO alerts (customer_id, risk_level, probability, alert_date, alert_status, message)
        VALUES 
        ('CUST-1001', 'High Risk', 78.4, ?, 'Pending', 'Dear Customer CUST-1001, your payment of $3,913 is 60 days past due. Please make a payment to prevent credit default.'),
        ('CUST-1002', 'High Risk', 64.2, ?, 'Pending', 'Dear Customer CUST-1002, our records indicate payment delays. Please contact customer care or settle your minimum due.')
    """, (datetime.now().strftime("%Y-%m-%d %H:%M"), datetime.now().strftime("%Y-%m-%d %H:%M")))

    conn.commit()


def get_dashboard_stats():
    """Computes total counts for the 5 dashboard metric cards."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE risk_category = 'Low Risk'")
    low_risk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE risk_category = 'Moderate Risk'")
    moderate_risk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE risk_category = 'High Risk'")
    high_risk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE review_status IN ('Reviewed', 'Whitelisted')")
    reviewed = cursor.fetchone()[0]

    conn.close()

    return {
        "total_customers": total_customers,
        "low_risk": low_risk,
        "moderate_risk": moderate_risk,
        "high_risk": high_risk,
        "reviewed_customers": reviewed
    }


def save_customer_prediction(customer_data):
    """Saves or updates a customer risk prediction."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if customer already exists
    cursor.execute("SELECT review_status FROM customers WHERE customer_id = ?", (customer_data["customer_id"],))
    existing = cursor.fetchone()
    status = existing["review_status"] if existing else "Not Reviewed"

    cursor.execute("""
        INSERT INTO customers (
            customer_id, probability, prediction, risk_category, review_status,
            limit_bal, age, pay_1, bill_amt1, pay_amt1, top_reasons, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(customer_id) DO UPDATE SET
            probability = excluded.probability,
            prediction = excluded.prediction,
            risk_category = excluded.risk_category,
            limit_bal = excluded.limit_bal,
            age = excluded.age,
            pay_1 = excluded.pay_1,
            bill_amt1 = excluded.bill_amt1,
            pay_amt1 = excluded.pay_amt1,
            top_reasons = excluded.top_reasons,
            created_at = excluded.created_at
    """, (
        customer_data["customer_id"],
        customer_data["probability"],
        customer_data["prediction"],
        customer_data["risk_category"],
        status,
        customer_data.get("limit_bal", 0),
        customer_data.get("age", 0),
        customer_data.get("pay_1", 0),
        customer_data.get("bill_amt1", 0),
        customer_data.get("pay_amt1", 0),
        json.dumps(customer_data.get("top_reasons", [])),
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    # If customer is High Risk, automatically create a risk alert if not already pending
    if customer_data["risk_category"] == "High Risk":
        cursor.execute("SELECT id FROM alerts WHERE customer_id = ? AND alert_status = 'Pending'", (customer_data["customer_id"],))
        alert_exists = cursor.fetchone()
        if not alert_exists:
            msg = f"Payment Reminder: Customer {customer_data['customer_id']} shows a default risk of {customer_data['probability']}%. Recommended immediate credit review."
            cursor.execute("""
                INSERT INTO alerts (customer_id, risk_level, probability, alert_date, alert_status, message)
                VALUES (?, ?, ?, ?, 'Pending', ?)
            """, (customer_data["customer_id"], customer_data["risk_category"], customer_data["probability"], datetime.now().strftime("%Y-%m-%d %H:%M"), msg))

    conn.commit()
    conn.close()


def get_all_customers(search="", risk_filter="All"):
    """Fetches customer records with optional search and risk filtering."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM customers WHERE 1=1"
    params = []

    if search:
        query += " AND customer_id LIKE ?"
        params.append(f"%{search}%")

    if risk_filter and risk_filter != "All":
        query += " AND risk_category = ?"
        params.append(risk_filter)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    customers = []
    for r in rows:
        customers.append({
            "id": r["id"],
            "customer_id": r["customer_id"],
            "probability": r["probability"],
            "prediction": r["prediction"],
            "risk_category": r["risk_category"],
            "review_status": r["review_status"],
            "limit_bal": r["limit_bal"],
            "age": r["age"],
            "pay_1": r["pay_1"],
            "bill_amt1": r["bill_amt1"],
            "pay_amt1": r["pay_amt1"],
            "top_reasons": json.loads(r["top_reasons"]) if r["top_reasons"] else [],
            "created_at": r["created_at"]
        })

    conn.close()
    return customers


def get_customer_by_id(customer_id):
    """Fetches a single customer record by customer_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    r = cursor.fetchone()
    conn.close()
    if r:
        return {
            "id": r["id"],
            "customer_id": r["customer_id"],
            "probability": r["probability"],
            "prediction": r["prediction"],
            "risk_category": r["risk_category"],
            "review_status": r["review_status"],
            "limit_bal": r["limit_bal"],
            "age": r["age"],
            "pay_1": r["pay_1"],
            "bill_amt1": r["bill_amt1"],
            "pay_amt1": r["pay_amt1"],
            "top_reasons": json.loads(r["top_reasons"]) if r["top_reasons"] else [],
            "created_at": r["created_at"]
        }
    return None


def add_to_whitelist(customer_id, reason, notes=""):
    """Adds a customer to the whitelist table and updates their review status."""
    conn = get_connection()
    cursor = conn.cursor()

    # Insert into whitelist
    cursor.execute("""
        INSERT INTO whitelist (customer_id, reason, notes, added_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(customer_id) DO UPDATE SET
            reason = excluded.reason,
            notes = excluded.notes,
            added_at = excluded.added_at
    """, (customer_id, reason, notes, datetime.now().strftime("%Y-%m-%d %H:%M")))

    # Update customer record review status
    cursor.execute("UPDATE customers SET review_status = 'Whitelisted' WHERE customer_id = ?", (customer_id,))

    conn.commit()
    conn.close()


def get_whitelist():
    """Returns all whitelisted customers."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT w.*, c.probability, c.risk_category 
        FROM whitelist w
        LEFT JOIN customers c ON w.customer_id = c.customer_id
        ORDER BY w.id DESC
    """)
    rows = cursor.fetchall()
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "customer_id": r["customer_id"],
            "reason": r["reason"],
            "notes": r["notes"],
            "added_at": r["added_at"],
            "probability": r["probability"] if r["probability"] is not None else 0.0,
            "risk_category": r["risk_category"] if r["risk_category"] else "High Risk"
        })
    conn.close()
    return result


def remove_from_whitelist(customer_id):
    """Removes a customer from whitelist and sets review_status to 'Reviewed'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM whitelist WHERE customer_id = ?", (customer_id,))
    cursor.execute("UPDATE customers SET review_status = 'Reviewed' WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()


def mark_customer_reviewed(customer_id):
    """Marks a customer as 'Reviewed'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET review_status = 'Reviewed' WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()


def get_all_alerts():
    """Fetches all customer risk alerts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY id DESC")
    rows = cursor.fetchall()
    alerts = []
    for r in rows:
        alerts.append({
            "id": r["id"],
            "customer_id": r["customer_id"],
            "risk_level": r["risk_level"],
            "probability": r["probability"],
            "alert_date": r["alert_date"],
            "alert_status": r["alert_status"],
            "message": r["message"]
        })
    conn.close()
    return alerts


def update_alert(alert_id, new_status, new_message=None):
    """Updates an alert status and message."""
    conn = get_connection()
    cursor = conn.cursor()
    if new_message:
        cursor.execute("UPDATE alerts SET alert_status = ?, message = ? WHERE id = ?", (new_status, new_message, alert_id))
    else:
        cursor.execute("UPDATE alerts SET alert_status = ? WHERE id = ?", (new_status, alert_id))
    conn.commit()
    conn.close()


def delete_customer_record(customer_id):
    """Deletes a customer record from customers, whitelist, and alerts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
    cursor.execute("DELETE FROM whitelist WHERE customer_id = ?", (customer_id,))
    cursor.execute("DELETE FROM alerts WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()

