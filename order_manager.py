"""
Logistics Order Manager Module
------------------------------
Primary business logic for order registration, updating, deletion,
searching, filtering, and validation against logistics domain rules.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from database import (
    add_order as db_add_order,
    update_order as db_update_order,
    delete_order as db_delete_order,
    get_orders as db_get_orders,
    get_order_by_id as db_get_order_by_id,
    order_exists as db_order_exists,
    record_delivery_completion as db_record_delivery
)
from deadline_calculator import parse_datetime, format_datetime

VALID_PRIORITIES = ["Critical", "High", "Medium", "Low"]
VALID_STATUSES = ["Pending", "Scheduled", "In Transit", "Delivered", "Delayed", "Cancelled"]


def validate_order(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, str]:
    """
    Validate business rules for an order:
    1. Order ID must be non-empty and unique (for new orders)
    2. Customer Name, Location, and Destination must be non-empty
    3. Processing time must be positive (> 0)
    4. Package weight and quantity must be positive (> 0)
    5. Priority must be one of: Critical, High, Medium, Low
    6. Status must be one of: Pending, Scheduled, In Transit, Delivered, Delayed, Cancelled
    7. Delivery deadline must be strictly after the order date
    """
    order_id = str(data.get("order_id", "")).strip()
    if not order_id:
        return False, "Order ID cannot be empty."

    if not is_update and db_order_exists(order_id):
        return False, f"Order ID '{order_id}' already exists in the database. Please use a unique Order ID."

    customer_name = str(data.get("customer_name", "")).strip()
    if not customer_name:
        return False, "Customer Name is required."

    customer_location = str(data.get("customer_location", "")).strip()
    if not customer_location:
        return False, "Customer Origin Location is required."

    destination = str(data.get("destination", "")).strip()
    if not destination:
        return False, "Delivery Destination is required."

    # Validate Priority
    priority = str(data.get("priority", "")).strip().capitalize()
    if priority not in VALID_PRIORITIES:
        return False, f"Invalid priority '{priority}'. Must be one of: {', '.join(VALID_PRIORITIES)}."

    # Validate Status
    status = str(data.get("delivery_status", "")).strip()
    # Normalize title case e.g. "In Transit"
    status_matched = next((s for s in VALID_STATUSES if s.lower() == status.lower()), None)
    if not status_matched:
        return False, f"Invalid delivery status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}."
    data["delivery_status"] = status_matched

    # Validate Numerical Fields
    try:
        proc_time = float(data.get("processing_time", 0.0))
        if proc_time <= 0:
            return False, "Processing time must be a positive number greater than 0 minutes."
    except (ValueError, TypeError):
        return False, "Processing time must be a valid positive number."

    try:
        weight = float(data.get("package_weight", 0.0))
        if weight <= 0:
            return False, "Package weight must be a positive number greater than 0 kg."
    except (ValueError, TypeError):
        return False, "Package weight must be a valid positive number."

    try:
        qty = int(data.get("package_quantity", 0))
        if qty <= 0:
            return False, "Package quantity must be at least 1 unit."
    except (ValueError, TypeError):
        return False, "Package quantity must be a positive whole integer."

    # Validate Dates
    order_date = data.get("order_date")
    deadline = data.get("delivery_deadline")

    if not order_date:
        return False, "Order date is required."
    if not deadline:
        return False, "Delivery deadline is required."

    order_dt = parse_datetime(order_date)
    deadline_dt = parse_datetime(deadline)

    if deadline_dt <= order_dt:
        return False, "Delivery deadline must be strictly after the order date."

    return True, "Validation successful."


def add_order(order_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate and insert a new delivery order.
    Returns (True, success_msg) or (False, error_msg).
    """
    is_valid, msg = validate_order(order_data, is_update=False)
    if not is_valid:
        return False, msg

    # Set expected delivery date if missing
    if not order_data.get("expected_delivery_date"):
        dl_dt = parse_datetime(order_data["delivery_deadline"])
        order_data["expected_delivery_date"] = format_datetime(dl_dt - timedelta(hours=1))

    success = db_add_order(order_data)
    if success:
        return True, f"Order '{order_data['order_id']}' added successfully."
    return False, "Database insertion failed. Duplicate ID or database error."


def update_order(order_id: str, order_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate and update an existing delivery order.
    Returns (True, success_msg) or (False, error_msg).
    """
    is_valid, msg = validate_order(order_data, is_update=True)
    if not is_valid:
        return False, msg

    if not order_data.get("expected_delivery_date"):
        dl_dt = parse_datetime(order_data["delivery_deadline"])
        order_data["expected_delivery_date"] = format_datetime(dl_dt - timedelta(hours=1))

    success = db_update_order(order_id, order_data)
    if success:
        return True, f"Order '{order_id}' updated successfully."
    return False, f"Could not update Order '{order_id}'. Record not found."


def delete_order(order_id: str) -> Tuple[bool, str]:
    """
    Delete an order and related schedule/delivery entries.
    Returns (True, success_msg) or (False, error_msg).
    """
    if not db_order_exists(order_id):
        return False, f"Order '{order_id}' does not exist."

    success = db_delete_order(order_id)
    if success:
        return True, f"Order '{order_id}' has been permanently deleted."
    return False, f"Failed to delete Order '{order_id}'."


def get_orders(
    search: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    destination: Optional[str] = None,
    deadline_from: Optional[str] = None,
    deadline_to: Optional[str] = None,
    sort_by: str = "deadline_asc"
) -> List[Dict[str, Any]]:
    """
    Retrieve orders with comprehensive multi-criteria filtering:
    - Search by Order ID, customer, or destination
    - Priority filter (Critical, High, Medium, Low)
    - Status filter (Pending, Scheduled, In Transit, Delivered, Delayed, Cancelled)
    - Destination city filter
    - Deadline range (deadline_from, deadline_to)
    - Sort order (deadline_asc, deadline_desc, priority_desc, date_desc, order_id)
    """
    return db_get_orders(
        search_term=search,
        priority_filter=priority,
        status_filter=status,
        destination_filter=destination,
        deadline_from=deadline_from,
        deadline_to=deadline_to,
        sort_by=sort_by
    )


def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """Fetch single order by ID."""
    return db_get_order_by_id(order_id)


def get_deadline_alerts(hours_threshold: float = 12.0) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan active orders to find orders approaching deadline or already overdue.
    Returns: {'overdue': [...], 'due_soon': [...]}
    """
    all_orders = db_get_orders(status_filter="All")
    now = datetime.now()
    threshold = now + timedelta(hours=hours_threshold)

    overdue: List[Dict[str, Any]] = []
    due_soon: List[Dict[str, Any]] = []

    for ord_dict in all_orders:
        if ord_dict["delivery_status"] in ["Delivered", "Cancelled"]:
            continue

        dl_dt = parse_datetime(ord_dict["delivery_deadline"])
        if dl_dt < now:
            diff_h = (now - dl_dt).total_seconds() / 3600.0
            ord_dict["overdue_hours"] = round(diff_h, 1)
            overdue.append(ord_dict)
        elif dl_dt <= threshold:
            slack_h = (dl_dt - now).total_seconds() / 3600.0
            ord_dict["remaining_hours"] = round(slack_h, 1)
            due_soon.append(ord_dict)

    return {"overdue": overdue, "due_soon": due_soon}
