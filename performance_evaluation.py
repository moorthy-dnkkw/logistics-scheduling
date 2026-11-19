"""
Delivery Performance Evaluation Module
---------------------------------------
Calculates formal logistics Key Performance Indicators (KPIs) and builds
interactive Plotly visualizations from actual database delivery records.

KPI Definitions and Denominators:
1. On-Time Delivery Rate:
   Numerator:   Count of orders delivered on or before deadline (on_time == 1)
   Denominator: Total delivered orders (on_time + late delivered)
   Formula:     (on_time_delivered / total_delivered) * 100

2. Late Delivery Rate:
   Numerator:   Count of late delivered orders (on_time == 0)
   Denominator: Total delivered orders (on_time + late delivered)
   Formula:     (late_delivered / total_delivered) * 100

3. Average Delivery Delay:
   Numerator:   Sum of delay hours across late delivered orders
   Denominator: Count of late delivered orders (late_delivered)
   Formula:     total_delay_hours / late_delivered_count

4. Average Waiting Time:
   Numerator:   Sum of waiting time hours for completed scheduled orders
   Denominator: Count of completed scheduled orders with waiting time records
   Formula:     total_waiting_hours / completed_scheduled_orders

5. Average Tardiness:
   Numerator:   Sum of positive lateness / tardiness hours across evaluated deliveries
   Denominator: Count of evaluated completed deliveries (total_delivered)
   Formula:     total_tardiness_hours / total_delivered

6. Deadline Compliance %:
   Numerator:   Deliveries completed within deadline
   Denominator: Evaluated completed deliveries
   Formula:     (compliant_deliveries / total_delivered) * 100

Note: Pending, Scheduled, and In Transit orders are NOT completed deliveries.
Future deadlines are NOT successes. Cancelled orders are excluded from delivery metrics.
Empty datasets return safe zero values with no division-by-zero errors.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import database
from deadline_calculator import parse_datetime, format_datetime


def evaluate_delivery_performance(
    orders: Optional[List[Dict[str, Any]]] = None,
    delivery_records: Optional[List[Dict[str, Any]]] = None,
    schedules: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Compute delivery performance KPIs with explicit denominators.
    Can be supplied with in-memory test fixtures or default to database queries.
    """
    if orders is None:
        orders = database.get_orders(status_filter="All")
    if delivery_records is None:
        delivery_records = database.get_delivery_records()
    if schedules is None:
        schedules = database.get_latest_schedule()

    # Counts by status across all orders
    total_orders = len(orders)
    pending_count = sum(1 for o in orders if o.get("delivery_status") == "Pending")
    scheduled_count = sum(1 for o in orders if o.get("delivery_status") == "Scheduled")
    transit_count = sum(1 for o in orders if o.get("delivery_status") == "In Transit")
    cancelled_count = sum(1 for o in orders if o.get("delivery_status") == "Cancelled")
    delivered_status_count = sum(1 for o in orders if o.get("delivery_status") == "Delivered")
    delayed_status_count = sum(1 for o in orders if o.get("delivery_status") == "Delayed")

    # Evaluated completed deliveries come strictly from delivery_records
    # (or orders with status Delivered / Delayed)
    # A delivery record is completed only if actual_delivery_time exists
    completed_deliveries = [
        r for r in delivery_records 
        if r.get("actual_delivery_time") and r.get("delivery_status") in ["Delivered", "Delayed"]
    ]

    total_delivered = len(completed_deliveries)
    on_time_count = sum(1 for r in completed_deliveries if int(r.get("on_time", 0)) == 1)
    late_count = sum(1 for r in completed_deliveries if int(r.get("on_time", 0)) == 0)

    # 1. On-Time Delivery Rate
    # Denominator: Total completed delivered orders
    if total_delivered > 0:
        on_time_delivery_rate = round((on_time_count / total_delivered) * 100.0, 1)
    else:
        on_time_delivery_rate = 0.0

    # 2. Late Delivery Rate
    # Denominator: Total completed delivered orders
    if total_delivered > 0:
        late_delivery_rate = round((late_count / total_delivered) * 100.0, 1)
    else:
        late_delivery_rate = 0.0

    # 3. Average Delivery Delay
    # Denominator: Number of late delivered orders only
    late_delays = [float(r.get("delay_duration_hours", 0.0)) for r in completed_deliveries if int(r.get("on_time", 0)) == 0]
    if late_count > 0:
        average_delivery_delay = round(sum(late_delays) / late_count, 2)
    else:
        average_delivery_delay = 0.0

    # 4. Average Waiting Time
    # Denominator: Count of completed scheduled orders with waiting time records
    if schedules:
        waiting_times = [float(s.get("waiting_time_hours", 0.0)) for s in schedules if "waiting_time_hours" in s]
        if waiting_times:
            average_waiting_time = round(sum(waiting_times) / len(waiting_times), 2)
        else:
            average_waiting_time = 0.0
    else:
        average_waiting_time = 0.0

    # 5. Average Tardiness
    # Denominator: Total completed delivered orders
    # Positive lateness in hours across all completed orders
    total_lateness = sum(float(r.get("delay_duration_hours", 0.0)) for r in completed_deliveries)
    if total_delivered > 0:
        average_tardiness = round(total_lateness / total_delivered, 2)
    else:
        average_tardiness = 0.0

    # 6. Deadline Compliance %
    # Denominator: Total completed delivered orders
    if total_delivered > 0:
        deadline_compliance_pct = round((on_time_count / total_delivered) * 100.0, 1)
    else:
        deadline_compliance_pct = 0.0

    return {
        "total_orders": total_orders,
        "delivered_orders": on_time_count,
        "delayed_orders": late_count,
        "total_completed_deliveries": total_delivered,
        "pending_orders": pending_count,
        "scheduled_orders": scheduled_count,
        "in_transit_orders": transit_count,
        "cancelled_orders": cancelled_count,
        "on_time_delivery_rate": on_time_delivery_rate,
        "late_delivery_rate": late_delivery_rate,
        "average_delivery_delay_hours": average_delivery_delay,
        "average_waiting_time_hours": average_waiting_time,
        "average_tardiness_hours": average_tardiness,
        "deadline_compliance_pct": deadline_compliance_pct
    }


# ----------------- PLOTLY VISUALIZATIONS -----------------

def _empty_figure(title: str, message: str = "No data available for the selected filters.") -> go.Figure:
    """Create a styled empty state figure when no data is available."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=13, color="#94A3B8")
    )
    fig.update_layout(
        title=f"<b>{title}</b>",
        plot_bgcolor="#111827",
        paper_bgcolor="#1E293B",
        font=dict(color="#E2E8F0"),
        height=280,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


def chart_ontime_vs_late(delivery_records: List[Dict[str, Any]]) -> go.Figure:
    """Chart 1: On-Time vs Late Deliveries Donut Chart."""
    if not delivery_records:
        return _empty_figure("On-Time vs Late Deliveries", "No completed deliveries found.")

    on_time = sum(1 for r in delivery_records if int(r.get("on_time", 0)) == 1)
    late = sum(1 for r in delivery_records if int(r.get("on_time", 0)) == 0)

    if on_time == 0 and late == 0:
        return _empty_figure("On-Time vs Late Deliveries", "No completed deliveries found.")

    fig = px.pie(
        names=["On-Time", "Delayed"],
        values=[on_time, late],
        color=["On-Time", "Delayed"],
        color_discrete_map={"On-Time": "#10B981", "Delayed": "#EF4444"},
        hole=0.55,
        title="<b>Delivery Punctuality Ratio</b>"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#1E293B",
        font=dict(color="#E2E8F0"),
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    return fig


def chart_status_distribution(orders: List[Dict[str, Any]]) -> go.Figure:
    """Chart 2: Order Delivery Status Breakdown Bar Chart."""
    if not orders:
        return _empty_figure("Delivery Status Breakdown")

    df = pd.DataFrame(orders)
    status_counts = df["delivery_status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    color_map = {
        "Delivered": "#10B981",
        "Delayed": "#EF4444",
        "In Transit": "#A855F7",
        "Scheduled": "#3B82F6",
        "Pending": "#F59E0B",
        "Cancelled": "#6B7280"
    }

    fig = px.bar(
        status_counts,
        x="Status",
        y="Count",
        color="Status",
        color_discrete_map=color_map,
        text="Count",
        title="<b>Current Consignment Status Breakdown</b>"
    )
    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#1E293B",
        font=dict(color="#E2E8F0"),
        showlegend=False,
        height=280,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


def chart_performance_over_time(delivery_records: List[Dict[str, Any]]) -> go.Figure:
    """Chart 3: Delivery Performance Over Time Line Chart."""
    if not delivery_records:
        return _empty_figure("Historical Performance Trend", "No historical delivery timestamps found.")

    records_with_date = []
    for r in delivery_records:
        dt_str = r.get("actual_delivery_time")
        if dt_str:
            d_only = str(dt_str)[:10]
            records_with_date.append({
                "Date": d_only,
                "OnTime": 1 if int(r.get("on_time", 0)) == 1 else 0,
                "Total": 1
            })

    if not records_with_date:
        return _empty_figure("Historical Performance Trend")

    df = pd.DataFrame(records_with_date)
    grouped = df.groupby("Date").agg({"OnTime": "sum", "Total": "count"}).reset_index()
    grouped["OnTimeRate"] = (grouped["OnTime"] / grouped["Total"]) * 100.0

    fig = px.line(
        grouped,
        x="Date",
        y="OnTimeRate",
        markers=True,
        title="<b>On-Time Delivery Rate Trend (%)</b>",
        labels={"OnTimeRate": "On-Time Rate (%)", "Date": "Delivery Date"}
    )
    fig.update_traces(line_color="#38BDF8", line_width=3, marker=dict(size=8, color="#0EA5E9"))
    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#1E293B",
        font=dict(color="#E2E8F0"),
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(range=[0, 105])
    )
    return fig


def chart_algorithm_comparison(scheduling_history: List[Dict[str, Any]]) -> go.Figure:
    """Chart 4: Scheduling Algorithm Performance Comparison Bar Chart."""
    if not scheduling_history:
        return _empty_figure("Algorithm Benchmarks", "No historical scheduling runs logged yet.")

    df = pd.DataFrame(scheduling_history)
    # Take latest run per algorithm
    latest_by_algo = df.drop_duplicates(subset=["algorithm"], keep="first")

    fig = px.bar(
        latest_by_algo,
        x="algorithm",
        y="on_time_feasibility_pct",
        color="algorithm",
        color_discrete_sequence=["#38BDF8", "#10B981", "#A855F7"],
        text="on_time_feasibility_pct",
        title="<b>Algorithm On-Time Feasibility Benchmark (%)</b>",
        labels={"algorithm": "Algorithm", "on_time_feasibility_pct": "Feasibility (%)"}
    )
    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#1E293B",
        font=dict(color="#E2E8F0"),
        showlegend=False,
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(range=[0, 105])
    )
    return fig


def chart_delay_by_priority(delivery_records: List[Dict[str, Any]]) -> go.Figure:
    """Chart 5: Average Delay Duration by Shipment Priority Bar Chart."""
    if not delivery_records:
        return _empty_figure("Average Delay by Priority", "No delivery records found.")

    prio_delays: Dict[str, List[float]] = {"Critical": [], "High": [], "Medium": [], "Low": []}

    for r in delivery_records:
        prio = str(r.get("priority", "Medium")).strip().capitalize()
        delay_h = float(r.get("delay_duration_hours", 0.0))
        if prio in prio_delays:
            prio_delays[prio].append(delay_h)

    rows = []
    for p, delays in prio_delays.items():
        avg = round(sum(delays) / len(delays), 2) if delays else 0.0
        rows.append({"Priority": p, "AverageDelayHours": avg})

    df = pd.DataFrame(rows)
    color_map = {
        "Critical": "#EF4444",
        "High": "#F97316",
        "Medium": "#F59E0B",
        "Low": "#94A3B8"
    }

    fig = px.bar(
        df,
        x="Priority",
        y="AverageDelayHours",
        color="Priority",
        color_discrete_map=color_map,
        text="AverageDelayHours",
        title="<b>Average Delay by Shipment Priority (Hours)</b>",
        labels={"AverageDelayHours": "Avg Delay (Hrs)"}
    )
    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#1E293B",
        font=dict(color="#E2E8F0"),
        showlegend=False,
        height=280,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


def chart_daily_completions(delivery_records: List[Dict[str, Any]]) -> go.Figure:
    """Chart 6: Daily Completed Deliveries Trend Line Chart."""
    if not delivery_records:
        return _empty_figure("Daily Completion Trend", "No completed deliveries recorded.")

    records_with_date = []
    for r in delivery_records:
        dt_str = r.get("actual_delivery_time")
        if dt_str:
            d_only = str(dt_str)[:10]
            records_with_date.append({"Date": d_only})

    if not records_with_date:
        return _empty_figure("Daily Completion Trend")

    df = pd.DataFrame(records_with_date)
    grouped = df.groupby("Date").size().reset_index(name="CompletedCount")

    fig = px.line(
        grouped,
        x="Date",
        y="CompletedCount",
        markers=True,
        title="<b>Daily Completed Delivery Volume</b>",
        labels={"CompletedCount": "Packages Delivered", "Date": "Delivery Date"}
    )
    fig.update_traces(line_color="#10B981", line_width=3, marker=dict(size=8, color="#059669"))
    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#1E293B",
        font=dict(color="#E2E8F0"),
        height=280,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


# ----------------- INSIGHTS GENERATOR -----------------

def generate_performance_insights(
    kpi_metrics: Dict[str, Any],
    delivery_records: List[Dict[str, Any]],
    scheduling_history: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """
    Generate factual, data-backed operational observations.
    Emits sentences ONLY when verified by actual database records.
    Never generates generic, speculative, or invented statements.
    """
    insights: List[str] = []

    total_deliv = kpi_metrics.get("total_completed_deliveries", 0)
    if total_deliv == 0:
        return ["No delivery completion records are currently available to evaluate operational trends."]

    on_time_pct = kpi_metrics.get("on_time_delivery_rate", 0.0)
    on_time_count = kpi_metrics.get("delivered_orders", 0)
    late_count = kpi_metrics.get("delayed_orders", 0)

    # 1. Overall Delivery Performance Observation
    insights.append(
        f"The current operational On-Time Delivery Rate is {on_time_pct}% ({on_time_count} of {total_deliv} evaluated consignments arrived within deadline)."
    )

    # 2. Priority Delay Disparity Observation
    prio_delays: Dict[str, List[float]] = {}
    for r in delivery_records:
        prio = str(r.get("priority", "Medium")).strip().capitalize()
        delay_h = float(r.get("delay_duration_hours", 0.0))
        prio_delays.setdefault(prio, []).append(delay_h)

    prio_avgs = {p: sum(d) / len(d) for p, d in prio_delays.items() if d}
    if prio_avgs:
        max_prio = max(prio_avgs, key=prio_avgs.get)
        min_prio = min(prio_avgs, key=prio_avgs.get)
        if prio_avgs[max_prio] > 0 and max_prio != min_prio:
            insights.append(
                f"{max_prio}-priority shipments experienced the highest average delivery delay ({prio_avgs[max_prio]:.1f} hours), whereas {min_prio}-priority averaged {prio_avgs[min_prio]:.1f} hours."
            )
        elif all(v == 0.0 for v in prio_avgs.values()):
            insights.append("All completed shipments across all priority tiers were delivered with zero recorded delay.")

    # 3. Delay magnitude observation
    avg_delay = kpi_metrics.get("average_delivery_delay_hours", 0.0)
    if late_count > 0:
        insights.append(
            f"{late_count} delivered order(s) exceeded expected deadlines with an average delay of {avg_delay:.1f} hours."
        )

    # 4. Scheduling algorithm comparison observation (from actual history)
    if scheduling_history:
        best_run = max(scheduling_history, key=lambda x: float(x.get("on_time_feasibility_pct", 0.0)))
        insights.append(
            f"In recent dispatch scheduling executions, {best_run['algorithm']} achieved the highest feasibility at {best_run['on_time_feasibility_pct']}%."
        )

    return insights
