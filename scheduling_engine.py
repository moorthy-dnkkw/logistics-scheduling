"""
Scheduling Engine Module
------------------------
Core Operations Research logistics scheduling engine.
Implements:
1. First Come First Served (FCFS)
2. Earliest Due Date (EDD)
3. Deadline-Aware Priority Scheduling

Time Model:
- start = max(resource_free_time, arrival, window_start)
- completion = start + processing_time
- waiting = max(0, start - arrival)
- tardiness = max(0, completion - deadline)
- feasible = completion <= deadline

Priority Score (normalized weighted multi-attribute formulation):
  score = 0.40*urgency + 0.30*priority + 0.20*feasibility + 0.10*risk
  - urgency in [0, 1]: 1 - (remaining_time / total_window), overdue orders = 1.0 (maximum urgency)
  - priority in [0, 1]: Critical=1.00, High=0.75, Medium=0.50, Low=0.25
  - feasibility in [0, 1]: processing_time / remaining_time, measuring schedule tightness
  - risk in [0, 1]: destination distance and package payload factor
  - safe against divide-by-zero and negative values
"""

from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from deadline_calculator import (
    parse_datetime,
    format_datetime,
    calculate_priority_score,
    calculate_job_schedule,
    priority_to_weight
)
from database import save_schedule_results


def _filter_eligible_orders(orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Exclude Delivered and Cancelled orders from scheduling consideration."""
    return [
        dict(o) for o in orders 
        if str(o.get("delivery_status", "")).strip().capitalize() not in ["Delivered", "Cancelled"]
    ]


def _simulate_resource_queue(
    ordered_jobs: List[Dict[str, Any]],
    scheduling_start: datetime,
    num_resources: int = 1,
    algorithm_name: str = "FCFS"
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Simulate parallel multi-resource dispatch queue for N vehicles/workers.
    Assigns each job, in sequence order, to the earliest-available resource.

    Validation:
    - Zero or negative resources raises a clear ValueError.
    - Zero eligible jobs returns an empty result set cleanly without crashing.
    """
    if num_resources is None or int(num_resources) <= 0:
        raise ValueError(f"Number of vehicles/resources must be a positive integer greater than 0. Received: {num_resources}")

    n_res = int(num_resources)
    resources = {f"Vehicle-{i+1}": scheduling_start for i in range(n_res)}

    if not ordered_jobs:
        empty_metrics = {
            "total_orders": 0,
            "on_time_count": 0,
            "late_count": 0,
            "avg_completion_time_hours": 0.0,
            "avg_waiting_time_hours": 0.0,
            "avg_tardiness_hours": 0.0,
            "max_tardiness_hours": 0.0,
            "total_weighted_tardiness_hours": 0.0,
            "on_time_feasibility_pct": 0.0
        }
        return [], empty_metrics

    scheduled_results: List[Dict[str, Any]] = []

    total_waiting_mins = 0.0
    total_tardiness_mins = 0.0
    total_completion_mins = 0.0
    max_tardiness_mins = 0.0
    total_weighted_tardiness = 0.0
    on_time_count = 0
    late_count = 0

    for idx, order in enumerate(ordered_jobs, start=1):
        arrival_dt = parse_datetime(order["order_date"])
        deadline_dt = parse_datetime(order["delivery_deadline"])

        raw_proc = float(order.get("processing_time", 60.0))
        proc_minutes = max(0.0, raw_proc)

        # Assign to the earliest-available vehicle
        best_resource = min(resources, key=resources.get)
        res_free_time = resources[best_resource]

        # Calculate exact timings via the time model
        job_calc = calculate_job_schedule(
            arrival_time=arrival_dt,
            deadline=deadline_dt,
            processing_time_minutes=proc_minutes,
            resource_free_time=res_free_time,
            scheduling_window_start=scheduling_start
        )

        # Update vehicle availability
        resources[best_resource] = job_calc["expected_completion"]

        w_mins = job_calc["waiting_time_minutes"]
        t_mins = job_calc["tardiness_minutes"]
        c_mins = max(0.0, (job_calc["expected_completion"] - scheduling_start).total_seconds() / 60.0)

        total_waiting_mins += w_mins
        total_tardiness_mins += t_mins
        total_completion_mins += c_mins
        max_tardiness_mins = max(max_tardiness_mins, t_mins)

        p_wt = priority_to_weight(order.get("priority", "Medium"))
        total_weighted_tardiness += p_wt * t_mins

        if job_calc["is_feasible"]:
            on_time_count += 1
        else:
            late_count += 1

        # Transparent plain-language reasoning
        score_val = order.get("computed_priority_score", 0.0)
        prio_label = order.get("priority", "Medium")
        if algorithm_name == "FCFS":
            reason = f"Ranked #{idx} by arrival sequence ({format_datetime(arrival_dt)}). Dispatched to {best_resource}."
        elif algorithm_name == "EDD":
            reason = f"Ranked #{idx} by earliest deadline ({format_datetime(deadline_dt)}). Dispatched to {best_resource}."
        else:
            reason = f"Ranked #{idx} with Priority Score {score_val:.1f}/100 ({prio_label} priority). Dispatched to {best_resource}."

        result_row = {
            "order_id": order["order_id"],
            "sequence_num": idx,
            "resource_id": best_resource,
            "customer_name": order.get("customer_name", ""),
            "destination": order.get("destination", ""),
            "priority": prio_label,
            "order_date": format_datetime(arrival_dt),
            "delivery_deadline": format_datetime(deadline_dt),
            "processing_time_minutes": round(proc_minutes, 1),
            "processing_time_hours": round(proc_minutes / 60.0, 2),
            "priority_score": score_val,
            "scheduled_start": format_datetime(job_calc["scheduled_start"]),
            "expected_completion": format_datetime(job_calc["expected_completion"]),
            "start_dt": job_calc["scheduled_start"],
            "completion_dt": job_calc["expected_completion"],
            "waiting_time_hours": job_calc["waiting_time_hours"],
            "waiting_time_minutes": job_calc["waiting_time_minutes"],
            "tardiness_hours": job_calc["tardiness_hours"],
            "tardiness_minutes": job_calc["tardiness_minutes"],
            "earliness_hours": job_calc["earliness_hours"],
            "earliness_minutes": job_calc["earliness_minutes"],
            "is_feasible": job_calc["is_feasible"],
            "deadline_status": job_calc["deadline_status"],
            "decision_reason": reason
        }
        scheduled_results.append(result_row)

    total_jobs = len(ordered_jobs)
    summary_metrics = {
        "total_orders": total_jobs,
        "on_time_count": on_time_count,
        "late_count": late_count,
        "avg_completion_time_hours": round((total_completion_mins / max(1, total_jobs)) / 60.0, 2),
        "avg_waiting_time_hours": round((total_waiting_mins / max(1, total_jobs)) / 60.0, 2),
        "avg_tardiness_hours": round((total_tardiness_mins / max(1, total_jobs)) / 60.0, 2),
        "max_tardiness_hours": round(max_tardiness_mins / 60.0, 2),
        "total_weighted_tardiness_hours": round(total_weighted_tardiness / 60.0, 2),
        "on_time_feasibility_pct": round((on_time_count / max(1, total_jobs)) * 100.0, 1)
    }

    return scheduled_results, summary_metrics


def schedule_fcfs(
    orders: List[Dict[str, Any]],
    scheduling_start: datetime,
    num_resources: int = 1
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Algorithm 1: First Come First Served (FCFS).
    Sorts eligible delivery orders by registration/arrival date ascending.
    """
    eligible = _filter_eligible_orders(orders)
    sorted_orders = sorted(eligible, key=lambda x: parse_datetime(x["order_date"]))
    return _simulate_resource_queue(sorted_orders, scheduling_start, num_resources, "FCFS")


def schedule_edd(
    orders: List[Dict[str, Any]],
    scheduling_start: datetime,
    num_resources: int = 1
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Algorithm 2: Earliest Due Date (EDD).
    Sorts eligible delivery orders by delivery deadline ascending.
    Known in classical scheduling theory (Jackson's Rule) to minimize maximum tardiness.
    """
    eligible = _filter_eligible_orders(orders)
    sorted_orders = sorted(eligible, key=lambda x: parse_datetime(x["delivery_deadline"]))
    return _simulate_resource_queue(sorted_orders, scheduling_start, num_resources, "EDD")


def schedule_deadline_priority(
    orders: List[Dict[str, Any]],
    scheduling_start: datetime,
    num_resources: int = 1,
    weights: Optional[Dict[str, float]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Algorithm 3: Deadline-Aware Priority Scheduling.
    Computes explainable composite priority score:
      score = 0.40*urgency + 0.30*priority + 0.20*feasibility + 0.10*risk
    Orders sorted descending by Priority Score (ties broken by earliest deadline).
    """
    eligible = _filter_eligible_orders(orders)

    scored_orders = []
    for ord_dict in eligible:
        ord_copy = dict(ord_dict)
        raw_proc = float(ord_copy.get("processing_time", 60.0))

        score = calculate_priority_score(
            order_date_val=ord_copy["order_date"],
            deadline_val=ord_copy["delivery_deadline"],
            processing_time_minutes=raw_proc,
            priority=ord_copy.get("priority", "Medium"),
            destination=ord_copy.get("destination", "Local Hub"),
            package_weight=float(ord_copy.get("package_weight", 10.0)),
            scheduling_time=scheduling_start,
            weights=weights
        )
        ord_copy["computed_priority_score"] = score
        scored_orders.append(ord_copy)

    # Sort descending by priority score; secondary sort ascending by deadline
    sorted_orders = sorted(
        scored_orders,
        key=lambda x: (-x["computed_priority_score"], parse_datetime(x["delivery_deadline"]))
    )

    return _simulate_resource_queue(sorted_orders, scheduling_start, num_resources, "Deadline-Aware Priority")


def generate_schedule(
    orders: List[Dict[str, Any]],
    scheduling_start: datetime,
    num_resources: int = 1,
    algorithm: str = "Deadline-Aware Priority",
    weights: Optional[Dict[str, float]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
    """
    Execute selected scheduling algorithm, assign versioned run ID,
    and persist results safely to the database without overwriting previous runs.
    """
    algo_clean = str(algorithm).strip()
    if algo_clean == "FCFS":
        results, summary = schedule_fcfs(orders, scheduling_start, num_resources)
    elif algo_clean == "EDD":
        results, summary = schedule_edd(orders, scheduling_start, num_resources)
    else:
        results, summary = schedule_deadline_priority(orders, scheduling_start, num_resources, weights)

    # Versioned run ID e.g. RUN-20261118-214530-PRIO-a1b2
    timestamp_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    algo_tag = "FCFS" if algo_clean == "FCFS" else ("EDD" if algo_clean == "EDD" else "PRIO")
    run_id = f"RUN-{timestamp_str}-{algo_tag}-{uuid.uuid4().hex[:4].upper()}"

    # Persist to database
    save_schedule_results(run_id, algo_clean, results, summary)
    return results, summary, run_id


def compare_scheduling_algorithms(
    orders: List[Dict[str, Any]],
    scheduling_start: datetime,
    num_resources: int = 1
) -> Dict[str, Any]:
    """
    Execute FCFS, EDD, and Deadline-Aware Priority on the EXACT SAME eligible orders.
    Produces comprehensive side-by-side comparative evaluation metrics and
    honestly identifies the best performer for this specific scenario.
    """
    eligible = _filter_eligible_orders(orders)

    fcfs_res, fcfs_sum = schedule_fcfs(eligible, scheduling_start, num_resources)
    edd_res, edd_sum = schedule_edd(eligible, scheduling_start, num_resources)
    prio_res, prio_sum = schedule_deadline_priority(eligible, scheduling_start, num_resources)

    comparison_data = [
        {"Algorithm": "First Come First Served (FCFS)", "Key": "FCFS", "Metrics": fcfs_sum, "Results": fcfs_res},
        {"Algorithm": "Earliest Due Date (EDD)", "Key": "EDD", "Metrics": edd_sum, "Results": edd_res},
        {"Algorithm": "Deadline-Aware Priority Scheduling", "Key": "Priority", "Metrics": prio_sum, "Results": prio_res}
    ]

    # Evaluate best algorithm honestly based on On-Time Feasibility and Average Tardiness
    best_algo = max(
        comparison_data,
        key=lambda x: (x["Metrics"]["on_time_feasibility_pct"], -x["Metrics"]["avg_tardiness_hours"])
    )

    analysis_notes = []
    if edd_sum["on_time_feasibility_pct"] > fcfs_sum["on_time_feasibility_pct"]:
        diff = edd_sum["on_time_feasibility_pct"] - fcfs_sum["on_time_feasibility_pct"]
        analysis_notes.append(f"EDD achieved +{diff:.1f}% higher on-time feasibility than FCFS by ordering by deadline urgency.")
    elif edd_sum["on_time_feasibility_pct"] == fcfs_sum["on_time_feasibility_pct"]:
        analysis_notes.append("EDD and FCFS achieved identical on-time feasibility on this dataset.")

    if prio_sum["total_weighted_tardiness_hours"] < fcfs_sum["total_weighted_tardiness_hours"]:
        saved = fcfs_sum["total_weighted_tardiness_hours"] - prio_sum["total_weighted_tardiness_hours"]
        analysis_notes.append(f"Deadline-Aware Priority reduced total weighted tardiness by {saved:.1f} hours compared to FCFS, successfully safeguarding critical consignments.")

    return {
        "comparison_table": [
            {
                "Algorithm": item["Algorithm"],
                "Total Scheduled": item["Metrics"]["total_orders"],
                "Predicted On-Time": item["Metrics"]["on_time_count"],
                "Predicted Late": item["Metrics"]["late_count"],
                "On-Time Feasibility (%)": f"{item['Metrics']['on_time_feasibility_pct']}%",
                "Avg Completion (hrs)": item["Metrics"]["avg_completion_time_hours"],
                "Avg Waiting (hrs)": item["Metrics"]["avg_waiting_time_hours"],
                "Avg Tardiness (hrs)": item["Metrics"]["avg_tardiness_hours"],
                "Max Tardiness (hrs)": item["Metrics"]["max_tardiness_hours"],
                "Weighted Tardiness (hrs)": item["Metrics"]["total_weighted_tardiness_hours"]
            }
            for item in comparison_data
        ],
        "detailed_runs": {item["Key"]: item for item in comparison_data},
        "best_algorithm": best_algo["Algorithm"],
        "analysis_notes": analysis_notes
    }


def create_gantt_chart(schedule_results: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """
    Generate interactive Plotly Gantt timeline chart for scheduled orders.
    Each horizontal bar shows the start and completion window on its assigned vehicle,
    color-coded by feasibility status.
    """
    if not schedule_results:
        return None

    gantt_rows = []
    status_colors = {
        "On-Time Feasible": "#10B981",  # Green
        "At-Risk": "#F59E0B",           # Amber
        "Predicted Late": "#EF4444",    # Red
        "Overdue": "#DC2626"            # Dark Red
    }

    for item in schedule_results:
        gantt_rows.append({
            "Order ID": item["order_id"],
            "Customer": item["customer_name"],
            "Resource": item["resource_id"],
            "Start": item["start_dt"],
            "Finish": item["completion_dt"],
            "Status": item["deadline_status"],
            "Priority": item["priority"],
            "Deadline": item["delivery_deadline"],
            "PrepTime": f"{item['processing_time_minutes']} min"
        })

    df_gantt = pd.DataFrame(gantt_rows)

    fig = px.timeline(
        df_gantt,
        x_start="Start",
        x_end="Finish",
        y="Resource",
        color="Status",
        color_discrete_map=status_colors,
        hover_data=["Order ID", "Customer", "Priority", "PrepTime", "Deadline", "Status"],
        title="<b>Vehicle Dispatch & Execution Timeline (Gantt Chart)</b>"
    )

    fig.update_yaxes(autorange="reversed")  # First resource at top
    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#1E293B",
        font=dict(color="#E2E8F0"),
        height=320 + (len(df_gantt["Resource"].unique()) * 40),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(255, 255, 255, 0.08)",
        tickformat="%H:%M\n%d %b"
    )

    return fig
