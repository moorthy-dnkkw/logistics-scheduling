"""
Database Management Module
--------------------------
Handles persistent SQLite storage for logistics orders, schedules,
actual delivery records, and execution history. Uses parameterized queries
to ensure security and integrity.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

DB_DIR = os.path.join(os.path.dirname(__file__), "database")
DB_PATH = os.path.join(DB_DIR, "logistics.db")


def get_connection() -> sqlite3.Connection:
    """Return an active connection to the SQLite database with row factory enabled and foreign keys enforced."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """
    Initialize SQLite database tables if they do not exist.
    Preserves existing data across application reruns.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            customer_location TEXT NOT NULL,
            destination TEXT NOT NULL,
            order_date TEXT NOT NULL,
            processing_time REAL NOT NULL,
            expected_delivery_date TEXT NOT NULL,
            delivery_deadline TEXT NOT NULL,
            priority TEXT NOT NULL,
            package_weight REAL NOT NULL,
            package_quantity INTEGER NOT NULL,
            delivery_status TEXT NOT NULL,
            assigned_vehicle TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # 2. Schedules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            order_id TEXT NOT NULL,
            sequence_num INTEGER NOT NULL,
            resource_id TEXT NOT NULL,
            scheduled_start TEXT NOT NULL,
            expected_completion TEXT NOT NULL,
            waiting_time_hours REAL NOT NULL,
            tardiness_hours REAL NOT NULL,
            earliness_hours REAL NOT NULL,
            priority_score REAL NOT NULL,
            deadline_status TEXT NOT NULL,
            decision_reason TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (order_id)
        )
    """)

    # 3. Delivery Records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            actual_dispatch_time TEXT NOT NULL,
            actual_delivery_time TEXT NOT NULL,
            delivery_status TEXT NOT NULL,
            delay_duration_hours REAL NOT NULL,
            on_time INTEGER NOT NULL,
            delivery_notes TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (order_id)
        )
    """)

    # 4. Scheduling History table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduling_history (
            run_id TEXT PRIMARY KEY,
            run_timestamp TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            total_orders INTEGER NOT NULL,
            on_time_count INTEGER NOT NULL,
            late_count INTEGER NOT NULL,
            avg_completion_time_hours REAL NOT NULL,
            avg_waiting_time_hours REAL NOT NULL,
            avg_tardiness_hours REAL NOT NULL,
            max_tardiness_hours REAL NOT NULL,
            on_time_feasibility_pct REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------- ORDER OPERATIONS ----------------

def order_exists(order_id: str) -> bool:
    """Check if an order ID already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM orders WHERE order_id = ?", (order_id.strip(),))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def add_order(order: Dict[str, Any]) -> bool:
    """Insert a new delivery order into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        created_at = order.get("created_at", datetime.now().isoformat())
        cursor.execute("""
            INSERT INTO orders (
                order_id, customer_name, customer_location, destination,
                order_date, processing_time, expected_delivery_date,
                delivery_deadline, priority, package_weight,
                package_quantity, delivery_status, assigned_vehicle, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order["order_id"].strip(),
            order["customer_name"].strip(),
            order["customer_location"].strip(),
            order["destination"].strip(),
            str(order["order_date"]),
            float(order["processing_time"]),
            str(order["expected_delivery_date"]),
            str(order["delivery_deadline"]),
            order["priority"].strip(),
            float(order["package_weight"]),
            int(order["package_quantity"]),
            order["delivery_status"].strip(),
            order.get("assigned_vehicle", "Unassigned"),
            created_at
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_order(order_id: str, order: Dict[str, Any]) -> bool:
    """Update existing order information."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE orders SET
                customer_name = ?,
                customer_location = ?,
                destination = ?,
                order_date = ?,
                processing_time = ?,
                expected_delivery_date = ?,
                delivery_deadline = ?,
                priority = ?,
                package_weight = ?,
                package_quantity = ?,
                delivery_status = ?,
                assigned_vehicle = ?
            WHERE order_id = ?
        """, (
            order["customer_name"].strip(),
            order["customer_location"].strip(),
            order["destination"].strip(),
            str(order["order_date"]),
            float(order["processing_time"]),
            str(order["expected_delivery_date"]),
            str(order["delivery_deadline"]),
            order["priority"].strip(),
            float(order["package_weight"]),
            int(order["package_quantity"]),
            order["delivery_status"].strip(),
            order.get("assigned_vehicle", "Unassigned"),
            order_id.strip()
        ))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_order(order_id: str) -> bool:
    """Delete an order and related delivery records/schedules."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM delivery_records WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM schedules WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_orders(
    search_term: Optional[str] = None,
    priority_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    destination_filter: Optional[str] = None,
    deadline_from: Optional[str] = None,
    deadline_to: Optional[str] = None,
    sort_by: str = "deadline_asc"
) -> List[Dict[str, Any]]:
    """Retrieve orders with multi-criteria filtering (search, priority, status, destination, deadline range) and sorting."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM orders WHERE 1=1"
    params: List[Any] = []

    if search_term:
        term = f"%{search_term.strip()}%"
        query += " AND (order_id LIKE ? OR customer_name LIKE ? OR destination LIKE ?)"
        params.extend([term, term, term])

    if priority_filter and priority_filter != "All":
        query += " AND priority = ?"
        params.append(priority_filter)

    if status_filter and status_filter != "All":
        query += " AND delivery_status = ?"
        params.append(status_filter)

    if destination_filter and destination_filter != "All":
        query += " AND destination = ?"
        params.append(destination_filter)

    if deadline_from:
        query += " AND datetime(delivery_deadline) >= datetime(?)"
        params.append(str(deadline_from))

    if deadline_to:
        query += " AND datetime(delivery_deadline) <= datetime(?)"
        params.append(str(deadline_to))
        query += " AND destination = ?"
        params.append(destination_filter)

    # Sorting
    sort_options = {
        "deadline_asc": "ORDER BY datetime(delivery_deadline) ASC",
        "deadline_desc": "ORDER BY datetime(delivery_deadline) DESC",
        "date_desc": "ORDER BY datetime(order_date) DESC",
        "priority_desc": "ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 ELSE 5 END",
        "order_id": "ORDER BY order_id ASC"
    }
    query += " " + sort_options.get(sort_by, "ORDER BY datetime(delivery_deadline) ASC")

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """Fetch single order by order_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------- SCHEDULE OPERATIONS ----------------

def save_schedule_results(
    run_id: str,
    algorithm: str,
    schedule_rows: List[Dict[str, Any]],
    summary_metrics: Dict[str, Any]
) -> None:
    """Save generated schedule items and log scheduling run summary."""
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()

    # Clear previous run of same run_id if re-running
    cursor.execute("DELETE FROM schedules WHERE run_id = ?", (run_id,))

    for item in schedule_rows:
        cursor.execute("""
            INSERT INTO schedules (
                run_id, algorithm, order_id, sequence_num, resource_id,
                scheduled_start, expected_completion, waiting_time_hours,
                tardiness_hours, earliness_hours, priority_score,
                deadline_status, decision_reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            algorithm,
            item["order_id"],
            item["sequence_num"],
            item.get("resource_id", "Resource-1"),
            str(item["scheduled_start"]),
            str(item["expected_completion"]),
            float(item.get("waiting_time_hours", 0.0)),
            float(item.get("tardiness_hours", 0.0)),
            float(item.get("earliness_hours", 0.0)),
            float(item.get("priority_score", 0.0)),
            item.get("deadline_status", "On-Time Feasible"),
            item.get("decision_reason", ""),
            now_iso
        ))

    # Save summary to history
    cursor.execute("""
        INSERT OR REPLACE INTO scheduling_history (
            run_id, run_timestamp, algorithm, total_orders, on_time_count,
            late_count, avg_completion_time_hours, avg_waiting_time_hours,
            avg_tardiness_hours, max_tardiness_hours, on_time_feasibility_pct
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        now_iso,
        algorithm,
        summary_metrics.get("total_orders", len(schedule_rows)),
        summary_metrics.get("on_time_count", 0),
        summary_metrics.get("late_count", 0),
        summary_metrics.get("avg_completion_time_hours", 0.0),
        summary_metrics.get("avg_waiting_time_hours", 0.0),
        summary_metrics.get("avg_tardiness_hours", 0.0),
        summary_metrics.get("max_tardiness_hours", 0.0),
        summary_metrics.get("on_time_feasibility_pct", 0.0)
    ))

    conn.commit()
    conn.close()


def get_latest_schedule(algorithm: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve the most recent generated schedule records."""
    conn = get_connection()
    cursor = conn.cursor()
    if algorithm:
        cursor.execute("""
            SELECT s.*, o.customer_name, o.destination, o.delivery_deadline, o.priority, o.processing_time
            FROM schedules s
            JOIN orders o ON s.order_id = o.order_id
            WHERE s.algorithm = ?
            ORDER BY s.sequence_num ASC
        """, (algorithm,))
    else:
        cursor.execute("""
            SELECT s.*, o.customer_name, o.destination, o.delivery_deadline, o.priority, o.processing_time
            FROM schedules s
            JOIN orders o ON s.order_id = o.order_id
            WHERE s.run_id = (SELECT run_id FROM schedules ORDER BY created_at DESC LIMIT 1)
            ORDER BY s.sequence_num ASC
        """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_scheduling_history() -> List[Dict[str, Any]]:
    """Retrieve all logged scheduling run comparisons."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scheduling_history ORDER BY datetime(run_timestamp) DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ---------------- DELIVERY PERFORMANCE OPERATIONS ----------------

def record_delivery_completion(
    order_id: str,
    actual_dispatch_time: str,
    actual_delivery_time: str,
    notes: str = ""
) -> bool:
    """Record actual delivery completion for an order and evaluate lateness."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT delivery_deadline FROM orders WHERE order_id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            return False

        deadline_str = order["delivery_deadline"]
        from deadline_calculator import parse_datetime
        deadline_dt = parse_datetime(deadline_str)
        actual_dt = parse_datetime(actual_delivery_time)

        diff_seconds = (actual_dt - deadline_dt).total_seconds()
        is_on_time = 1 if diff_seconds <= 0 else 0
        delay_hours = max(0.0, diff_seconds / 3600.0)
        status = "Delivered" if is_on_time else "Delayed"

        cursor.execute("""
            INSERT OR REPLACE INTO delivery_records (
                order_id, actual_dispatch_time, actual_delivery_time,
                delivery_status, delay_duration_hours, on_time, delivery_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            actual_dispatch_time,
            actual_delivery_time,
            status,
            round(delay_hours, 2),
            is_on_time,
            notes
        ))

        # Also update orders table status
        cursor.execute("UPDATE orders SET delivery_status = ? WHERE order_id = ?", (status, order_id))
        conn.commit()
        return True
    finally:
        conn.close()


def get_delivery_records() -> List[Dict[str, Any]]:
    """Fetch all actual delivery records joined with order details."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, o.customer_name, o.customer_location, o.destination,
               o.order_date, o.delivery_deadline, o.priority, o.package_weight
        FROM delivery_records r
        JOIN orders o ON r.order_id = o.order_id
        ORDER BY datetime(r.actual_delivery_time) DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_kpis_summary() -> Dict[str, Any]:
    """
    Calculate high-level summary KPIs directly from persistent database records.
    Used for the primary landing dashboard cards.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM orders")
    total_orders = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE delivery_status = 'Delivered'")
    delivered_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE delivery_status = 'Delayed'")
    delayed_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE delivery_status = 'Pending'")
    pending_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE delivery_status = 'In Transit'")
    transit_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE delivery_status = 'Scheduled'")
    scheduled_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE delivery_status = 'Cancelled'")
    cancelled_count = cursor.fetchone()["count"]

    # Calculate actual On-time delivery rate from delivered + delayed
    total_completed = delivered_count + delayed_count
    if total_completed > 0:
        on_time_rate = round((delivered_count / total_completed) * 100.0, 1)
    else:
        on_time_rate = 0.0

    # Average delay
    cursor.execute("SELECT AVG(delay_duration_hours) as avg_delay FROM delivery_records WHERE on_time = 0")
    row_avg = cursor.fetchone()
    avg_delay = round(row_avg["avg_delay"], 1) if row_avg and row_avg["avg_delay"] is not None else 0.0

    conn.close()

    return {
        "total_orders": total_orders,
        "delivered_orders": delivered_count,
        "delayed_orders": delayed_count,
        "pending_orders": pending_count,
        "transit_orders": transit_count,
        "scheduled_orders": scheduled_count,
        "cancelled_orders": cancelled_count,
        "on_time_delivery_rate": on_time_rate,
        "average_delivery_delay_hours": avg_delay
    }


def reset_database() -> None:
    """Clear all records from all tables for clean demonstration resetting."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM delivery_records")
    cursor.execute("DELETE FROM schedules")
    cursor.execute("DELETE FROM scheduling_history")
    cursor.execute("DELETE FROM orders")
    conn.commit()
    conn.close()
