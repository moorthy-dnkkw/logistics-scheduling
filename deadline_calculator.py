"""
Deadline Calculator Engine
---------------------------
Core calculation utilities for deadline-aware logistics scheduling.
Implements the exact time model, queue simulation, and multi-criteria priority scoring.

Time Model:
- processing_time: duration in minutes for preparation / dispatch
- start = max(resource_free_time, arrival, scheduling_window_start)
- completion = start + processing_time
- waiting = max(0, (start - arrival).total_seconds() / 60.0)  [in minutes]
- tardiness = max(0, (completion - deadline).total_seconds() / 60.0) [in minutes]
- earliness = max(0, (deadline - completion).total_seconds() / 60.0) [in minutes]
- feasible = completion <= deadline
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional, List


def parse_datetime(dt_val: Any) -> datetime:
    """
    Safely parse datetime from string or datetime object.
    Supports ISO formats and standard database representations.
    """
    if isinstance(dt_val, datetime):
        return dt_val
    if not dt_val:
        return datetime.now()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d"
    ]
    str_val = str(dt_val).strip()
    for fmt in formats:
        try:
            return datetime.strptime(str_val, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(str_val)
    except Exception:
        return datetime.now()


def format_datetime(dt: datetime, include_seconds: bool = False) -> str:
    """Format datetime into consistent standard display string."""
    if include_seconds:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d %H:%M")


def priority_to_weight(priority: str) -> float:
    """
    Convert shipment priority into standardized normalized weight in [0.0, 1.0]:
    - Critical: 1.00
    - High:     0.75
    - Medium:   0.50
    - Low:      0.25
    """
    p = str(priority).strip().upper()
    mapping = {
        "CRITICAL": 1.00,
        "HIGH": 0.75,
        "MEDIUM": 0.50,
        "LOW": 0.25
    }
    return mapping.get(p, 0.50)


def calculate_deadline_urgency(
    order_date_val: Any,
    deadline_val: Any,
    scheduling_time: Optional[datetime] = None
) -> float:
    """
    Calculate Deadline Urgency factor in [0.0, 1.0].
    Measures how close an order is to its deadline relative to total allowed duration.
    
    Formula:
        Total Window = max(1 min, Deadline - Arrival)
        Remaining Window = Deadline - Scheduling Time
        If remaining <= 0: 1.0 (overdue / maximum urgency)
        Else: 1.0 - (Remaining / Total Window) bounded in [0.0, 1.0]
    """
    if scheduling_time is None:
        scheduling_time = datetime.now()

    arrival_dt = parse_datetime(order_date_val)
    deadline_dt = parse_datetime(deadline_val)

    total_minutes = max(1.0, (deadline_dt - arrival_dt).total_seconds() / 60.0)
    remaining_minutes = (deadline_dt - scheduling_time).total_seconds() / 60.0

    if remaining_minutes <= 0:
        return 1.0

    ratio = remaining_minutes / total_minutes
    urgency = 1.0 - max(0.0, min(1.0, ratio))
    return round(urgency, 4)


def calculate_processing_feasibility(
    processing_time_minutes: float,
    deadline_val: Any,
    scheduling_time: Optional[datetime] = None
) -> float:
    """
    Calculate Processing Feasibility factor in [0.0, 1.0].
    Measures the ratio of processing time needed to the remaining available time.
    When remaining time is tight compared to processing duration, this urgency rises.
    
    Formula:
        Remaining = Deadline - Scheduling Time
        If remaining <= 0: 1.0 (zero buffer / late)
        Else: min(1.0, max(0.0, processing_time_minutes / remaining))
    """
    if scheduling_time is None:
        scheduling_time = datetime.now()

    deadline_dt = parse_datetime(deadline_val)
    remaining_minutes = (deadline_dt - scheduling_time).total_seconds() / 60.0

    if remaining_minutes <= 0:
        return 1.0

    # Ensure non-negative processing time
    proc_mins = max(0.0, float(processing_time_minutes))
    ratio = proc_mins / max(1.0, remaining_minutes)
    return round(min(1.0, max(0.0, ratio)), 4)


def calculate_delivery_risk(
    destination: str,
    package_weight: float = 10.0
) -> float:
    """
    Calculate Delivery Risk in [0.0, 1.0] based on destination distance and payload.
    Indian logistics routes categorized by interstate distance / transit tiers.
    """
    tier_high_risk = ["DELHI", "KOLKATA", "MUMBAI", "AHMEDABAD"]
    dest_norm = str(destination).strip().upper()
    dest_factor = 0.75 if any(city in dest_norm for city in tier_high_risk) else 0.40

    # Weight factor: heavier shipments risk slower handling / loading
    safe_weight = max(0.1, float(package_weight))
    weight_factor = min(1.0, safe_weight / 200.0) * 0.25

    risk = min(1.0, max(0.0, dest_factor * 0.75 + weight_factor))
    return round(risk, 4)


def calculate_priority_score(
    order_date_val: Any,
    deadline_val: Any,
    processing_time_minutes: float,
    priority: str,
    destination: str = "Local Hub",
    package_weight: float = 10.0,
    scheduling_time: Optional[datetime] = None,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Compute normalized Deadline-Aware Priority Score in [0.0, 1.0] (and scaled to 100 for display).
    
    Formula:
        score = 0.40 * urgency + 0.30 * priority + 0.20 * feasibility + 0.10 * risk
        
    Guaranteed:
    - Every component is strictly in [0.0, 1.0]
    - Overdue orders explicitly get maximum urgency (1.0) and high feasibility pressure (1.0)
    - Division by zero is completely prevented
    - Returned score is rounded and non-negative
    """
    if scheduling_time is None:
        scheduling_time = datetime.now()

    if weights is None:
        weights = {
            "urgency": 0.40,
            "priority": 0.30,
            "feasibility": 0.20,
            "risk": 0.10
        }

    urgency = calculate_deadline_urgency(order_date_val, deadline_val, scheduling_time)
    priority_wt = priority_to_weight(priority)
    feasibility = calculate_processing_feasibility(processing_time_minutes, deadline_val, scheduling_time)
    risk = calculate_delivery_risk(destination, package_weight)

    composite = (
        (urgency * weights.get("urgency", 0.40)) +
        (priority_wt * weights.get("priority", 0.30)) +
        (feasibility * weights.get("feasibility", 0.20)) +
        (risk * weights.get("risk", 0.10))
    )

    # Scale to 0-100 for presentation
    score_100 = round(composite * 100.0, 2)
    return score_100


def calculate_job_schedule(
    arrival_time: datetime,
    deadline: datetime,
    processing_time_minutes: float,
    resource_free_time: datetime,
    scheduling_window_start: datetime,
    threshold_minutes: float = 60.0
) -> Dict[str, Any]:
    """
    Compute deterministic start, completion, waiting, tardiness, and feasibility
    for a single scheduled job according to the official time model.
    
    Model:
        start = max(resource_free_time, arrival, scheduling_window_start)
        completion = start + processing_time
        waiting = max(0, (start - arrival).total_seconds() / 60.0)
        tardiness = max(0, (completion - deadline).total_seconds() / 60.0)
        earliness = max(0, (deadline - completion).total_seconds() / 60.0)
        feasible = completion <= deadline
    """
    # Safe non-negative processing time
    proc_mins = max(0.0, float(processing_time_minutes))
    
    # start = max(resource_free_time, arrival, scheduling_window_start)
    start_time = max(resource_free_time, arrival_time, scheduling_window_start)
    completion_time = start_time + timedelta(minutes=proc_mins)

    # Waiting time in minutes
    waiting_mins = max(0.0, (start_time - arrival_time).total_seconds() / 60.0)

    # Tardiness and Earliness in minutes
    diff_from_deadline_mins = (completion_time - deadline).total_seconds() / 60.0
    tardiness_mins = max(0.0, diff_from_deadline_mins)
    earliness_mins = max(0.0, -diff_from_deadline_mins)

    is_feasible = completion_time <= deadline

    # Determine deadline status category
    if start_time > deadline:
        status = "Overdue"
        reason = f"Scheduled start ({format_datetime(start_time)}) is already past delivery deadline ({format_datetime(deadline)})."
    elif completion_time > deadline:
        status = "Predicted Late"
        reason = f"Completion exceeds deadline by {tardiness_mins:.1f} mins ({tardiness_mins/60.0:.1f} hrs)."
    elif (deadline - completion_time).total_seconds() / 60.0 <= threshold_minutes:
        status = "At-Risk"
        slack_mins = (deadline - completion_time).total_seconds() / 60.0
        reason = f"Tight delivery buffer: completes only {slack_mins:.1f} mins before deadline."
    else:
        status = "On-Time Feasible"
        slack_mins = (deadline - completion_time).total_seconds() / 60.0
        reason = f"Meets deadline with {slack_mins:.1f} mins ({slack_mins/60.0:.1f} hrs) buffer."

    return {
        "scheduled_start": start_time,
        "expected_completion": completion_time,
        "waiting_time_minutes": round(waiting_mins, 2),
        "waiting_time_hours": round(waiting_mins / 60.0, 2),
        "tardiness_minutes": round(tardiness_mins, 2),
        "tardiness_hours": round(tardiness_mins / 60.0, 2),
        "earliness_minutes": round(earliness_mins, 2),
        "earliness_hours": round(earliness_mins / 60.0, 2),
        "is_feasible": is_feasible,
        "deadline_status": status,
        "decision_reason": reason
    }


def calculate_waiting_time(start_time: Any, arrival_time: Any) -> float:
    """
    Calculate waiting time in minutes between job arrival and scheduled start.
    Formula: max(0.0, start_time - arrival_time)
    """
    start_dt = parse_datetime(start_time)
    arrival_dt = parse_datetime(arrival_time)
    diff = (start_dt - arrival_dt).total_seconds() / 60.0
    return round(max(0.0, diff), 2)


def calculate_tardiness(completion_time: Any, deadline: Any) -> float:
    """
    Calculate tardiness in minutes.
    Formula: max(0.0, completion_time - deadline)
    """
    comp_dt = parse_datetime(completion_time)
    dl_dt = parse_datetime(deadline)
    diff = (comp_dt - dl_dt).total_seconds() / 60.0
    return round(max(0.0, diff), 2)


def calculate_earliness(completion_time: Any, deadline: Any) -> float:
    """
    Calculate earliness in minutes.
    Formula: max(0.0, deadline - completion_time)
    """
    comp_dt = parse_datetime(completion_time)
    dl_dt = parse_datetime(deadline)
    diff = (dl_dt - comp_dt).total_seconds() / 60.0
    return round(max(0.0, diff), 2)


def is_deadline_feasible(completion_time: Any, deadline: Any) -> bool:
    """
    Check if a job completes on or before its delivery deadline.
    Formula: completion_time <= deadline
    """
    comp_dt = parse_datetime(completion_time)
    dl_dt = parse_datetime(deadline)
    return comp_dt <= dl_dt

