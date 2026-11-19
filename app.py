"""
Deadline-Aware Logistics Scheduling & Delivery Performance Evaluation
----------------------------------------------------------------------
Official Academic Demonstration Application
Tagline: Smarter Scheduling. Faster Deliveries. Measurable Performance.

Built with Python, Streamlit, Pandas, NumPy, Plotly, SQLite, and custom CSS.
"""

from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import database
import order_manager
import sample_data
from deadline_calculator import parse_datetime, format_datetime

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Deadline-Aware Logistics Scheduling",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Database on startup
database.init_db()

# Ensure session state for navigation
if "selected_module" not in st.session_state:
    st.session_state["selected_module"] = "MODULE 01 — Logistics Order Management"
if "edit_order_id" not in st.session_state:
    st.session_state["edit_order_id"] = None
if "delete_order_id" not in st.session_state:
    st.session_state["delete_order_id"] = None

# ----------------- CUSTOM LOGISTICS CSS -----------------
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main background */
    .stApp {
        background-color: #0B1120;
        color: #E2E8F0;
    }

    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 14px;
        padding: 28px 36px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #FFFFFF;
        margin-bottom: 6px;
        line-height: 1.25;
    }
    .hero-title span {
        color: #38BDF8;
    }
    .hero-tagline {
        font-size: 1.05rem;
        font-weight: 600;
        color: #38BDF8;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .hero-intro {
        font-size: 0.96rem;
        color: #94A3B8;
        line-height: 1.6;
        max-width: 950px;
        margin: 0;
    }

    /* KPI Stat Cards */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 26px;
    }
    .kpi-card {
        background: #1E293B;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px 20px;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    .kpi-label {
        font-size: 0.76rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1;
    }
    .kpi-subtext {
        font-size: 0.72rem;
        color: #64748B;
        margin-top: 5px;
    }

    /* Module Navigation Buttons Bar */
    .module-nav-container {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 28px;
    }

    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
    }

    /* Alert Banner */
    .alert-banner {
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 0.88rem;
    }
    .alert-overdue {
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.35);
        color: #FCA5A5;
    }
    .alert-warning {
        background: rgba(245, 158, 11, 0.12);
        border: 1px solid rgba(245, 158, 11, 0.35);
        color: #FCD34D;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-critical { background: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid #EF4444; }
    .badge-high { background: rgba(249, 115, 22, 0.2); color: #FB923C; border: 1px solid #F97316; }
    .badge-medium { background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid #F59E0B; }
    .badge-low { background: rgba(148, 163, 184, 0.2); color: #CBD5E1; border: 1px solid #64748B; }

    .badge-delivered { background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981; }
    .badge-delayed { background: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid #EF4444; }
    .badge-transit { background: rgba(168, 85, 247, 0.2); color: #C084FC; border: 1px solid #A855F7; }
    .badge-scheduled { background: rgba(59, 130, 246, 0.2); color: #60A5FA; border: 1px solid #3B82F6; }
    .badge-pending { background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid #F59E0B; }
    .badge-cancelled { background: rgba(107, 114, 128, 0.2); color: #9CA3AF; border: 1px solid #4B5563; }

    /* Forms & Containers */
    .card-box {
        background: #1E293B;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.15s ease;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ----------------- HEADER & HERO SECTION -----------------
st.markdown("""
<div class="hero-container">
    <div class="hero-tagline">Smarter Scheduling. Faster Deliveries. Measurable Performance.</div>
    <div class="hero-title">Deadline-Aware Logistics Scheduling &amp; <span>Delivery Performance Evaluation</span></div>
    <p class="hero-intro">
        An intelligent logistics management and scheduling platform designed to prioritize delivery orders, 
        manage deadline-sensitive shipments, and evaluate operational delivery performance through algorithm-driven decision-making.
    </p>
</div>
""", unsafe_allow_html=True)


# ----------------- DATABASE KPIS SUMMARY -----------------
kpis = database.get_kpis_summary()

col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
with col_k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Delivery Orders</div>
        <div class="kpi-value">{kpis['total_orders']}</div>
        <div class="kpi-subtext">Active & Historical Records</div>
    </div>
    """, unsafe_allow_html=True)

with col_k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">On-Time Deliveries</div>
        <div class="kpi-value" style="color: #34D399;">{kpis['delivered_orders']}</div>
        <div class="kpi-subtext">Completed within deadline</div>
    </div>
    """, unsafe_allow_html=True)

with col_k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Delayed Deliveries</div>
        <div class="kpi-value" style="color: #F87171;">{kpis['delayed_orders']}</div>
        <div class="kpi-subtext">Avg Delay: {kpis['average_delivery_delay_hours']} hrs</div>
    </div>
    """, unsafe_allow_html=True)

with col_k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Pending Orders</div>
        <div class="kpi-value" style="color: #FBBF24;">{kpis['pending_orders']}</div>
        <div class="kpi-subtext">Eligible for scheduling</div>
    </div>
    """, unsafe_allow_html=True)

with col_k5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">On-Time Delivery Rate</div>
        <div class="kpi-value" style="color: #38BDF8;">{kpis['on_time_delivery_rate']}%</div>
        <div class="kpi-subtext">{kpis['delivered_orders']} of {kpis['delivered_orders'] + kpis['delayed_orders']} completed</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# ----------------- EXACTLY THREE MODULE BUTTONS -----------------
MOD_1 = "MODULE 01 — Logistics Order Management"
MOD_2 = "MODULE 02 — Deadline-Aware Scheduling Optimization"
MOD_3 = "MODULE 03 — Delivery Performance Evaluation"

col_nav1, col_nav2, col_nav3, col_demo = st.columns([1.2, 1.3, 1.2, 1.0])

with col_nav1:
    is_active_1 = st.session_state["selected_module"] == MOD_1
    btn_type_1 = "primary" if is_active_1 else "secondary"
    if st.button("📦 " + MOD_1, use_container_width=True, type=btn_type_1):
        st.session_state["selected_module"] = MOD_1
        st.rerun()

with col_nav2:
    is_active_2 = st.session_state["selected_module"] == MOD_2
    btn_type_2 = "primary" if is_active_2 else "secondary"
    if st.button("⚡ " + MOD_2, use_container_width=True, type=btn_type_2):
        st.session_state["selected_module"] = MOD_2
        st.rerun()

with col_nav3:
    is_active_3 = st.session_state["selected_module"] == MOD_3
    btn_type_3 = "primary" if is_active_3 else "secondary"
    if st.button("📊 " + MOD_3, use_container_width=True, type=btn_type_3):
        st.session_state["selected_module"] = MOD_3
        st.rerun()

with col_demo:
    if st.button("🔄 Load Demo Data", use_container_width=True, help="Seed 25 realistic demonstration orders without duplicates"):
        count = sample_data.seed_demonstration_data(force=False)
        st.success(f"Demonstration data ready ({count} orders).")
        st.rerun()

st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 18px 0;'>", unsafe_allow_html=True)


# ----------------- MODULE ROUTING -----------------

# =========================================================================
# MODULE 01 — LOGISTICS ORDER MANAGEMENT
# =========================================================================
if st.session_state["selected_module"] == MOD_1:
    st.markdown("""
    <div class="section-header">
        <div>
            <h2 class="section-title">MODULE 01 — Logistics Order Management</h2>
            <p style="color: #94A3B8; font-size: 0.88rem; margin: 4px 0 0 0;">
                Register, update, monitor, and maintain delivery consignments with validated deadlines and shipment priorities.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Deadline Warnings Banner
    alerts = order_manager.get_deadline_alerts(hours_threshold=12.0)
    if alerts["overdue"]:
        overdue_ids = ", ".join([f"{o['order_id']} ({o.get('overdue_hours', 0)}h late)" for o in alerts["overdue"][:5]])
        st.markdown(f"""
        <div class="alert-banner alert-overdue">
            <strong>⚠️ CRITICAL DEADLINE VIOLATION:</strong> {len(alerts['overdue'])} order(s) already past delivery deadline: {overdue_ids}
        </div>
        """, unsafe_allow_html=True)

    if alerts["due_soon"]:
        soon_ids = ", ".join([f"{o['order_id']} ({o.get('remaining_hours', 0)}h left)" for o in alerts["due_soon"][:5]])
        st.markdown(f"""
        <div class="alert-banner alert-warning">
            <strong>⏰ APPROACHING DEADLINE ALERT:</strong> {len(alerts['due_soon'])} order(s) have under 12 hours remaining: {soon_ids}
        </div>
        """, unsafe_allow_html=True)

    # 2. Controls & Actions Bar
    with st.expander("➕ Register New Delivery Order", expanded=False):
        st.markdown("#### Delivery Order Registration Form")
        with st.form("form_add_order", clear_on_submit=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                # Auto-generate suggestion for Order ID
                suggested_id = f"ORD-{1000 + kpis['total_orders'] + 1}"
                new_id = st.text_input("Order ID *", value=suggested_id, help="Must be unique")
                new_cust = st.text_input("Customer Name *", placeholder="e.g. Apollo Pharmacy Hub")
                new_loc = st.text_input("Customer Origin Location *", placeholder="e.g. Guindy Industrial Zone, Chennai")
                new_dest = st.selectbox("Delivery Destination *", ["Chennai", "Bengaluru", "Coimbatore", "Hyderabad", "Mumbai", "Delhi", "Pune", "Kolkata", "Kochi", "Ahmedabad"])

            with f_col2:
                now_dt = datetime.now()
                new_order_date = st.date_input("Order Date", value=now_dt.date())
                new_order_time = st.time_input("Order Time", value=now_dt.time())
                new_proc_time = st.number_input("Preparation/Dispatch Time (Minutes) *", min_value=5.0, max_value=720.0, value=60.0, step=15.0, help="Operational preparation time in minutes")
                new_priority = st.selectbox("Shipment Priority *", order_manager.VALID_PRIORITIES, index=2)

            with f_col3:
                default_deadline = now_dt + timedelta(hours=24)
                new_dl_date = st.date_input("Delivery Deadline Date *", value=default_deadline.date())
                new_dl_time = st.time_input("Delivery Deadline Time *", value=default_deadline.time())
                new_weight = st.number_input("Package Weight (kg) *", min_value=0.1, max_value=2000.0, value=25.0, step=5.0)
                new_qty = st.number_input("Package Quantity *", min_value=1, max_value=500, value=10, step=1)
                new_status = st.selectbox("Initial Delivery Status", order_manager.VALID_STATUSES, index=0)
                new_vehicle = st.text_input("Assigned Delivery Vehicle (Optional)", value="Unassigned")

            submitted = st.form_submit_button("✅ Register Delivery Order", use_container_width=True)
            if submitted:
                full_order_dt = datetime.combine(new_order_date, new_order_time)
                full_dl_dt = datetime.combine(new_dl_date, new_dl_time)

                new_order_dict = {
                    "order_id": new_id.strip(),
                    "customer_name": new_cust.strip(),
                    "customer_location": new_loc.strip(),
                    "destination": new_dest.strip(),
                    "order_date": format_datetime(full_order_dt, include_seconds=True),
                    "processing_time": float(new_proc_time),
                    "expected_delivery_date": format_datetime(full_dl_dt - timedelta(hours=1), include_seconds=True),
                    "delivery_deadline": format_datetime(full_dl_dt, include_seconds=True),
                    "priority": new_priority,
                    "package_weight": float(new_weight),
                    "package_quantity": int(new_qty),
                    "delivery_status": new_status,
                    "assigned_vehicle": new_vehicle.strip() if new_vehicle else "Unassigned"
                }

                success, msg = order_manager.add_order(new_order_dict)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(f"Validation Error: {msg}")

    # 3. Edit Order Dialog / Form if an edit order is selected
    if st.session_state["edit_order_id"]:
        edit_target = order_manager.get_order_by_id(st.session_state["edit_order_id"])
        if edit_target:
            st.markdown(f"### ✏️ Edit Order Details: `{edit_target['order_id']}`")
            with st.form("form_edit_order"):
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    e_cust = st.text_input("Customer Name", value=edit_target["customer_name"])
                    e_loc = st.text_input("Customer Location", value=edit_target["customer_location"])
                    cities = ["Chennai", "Bengaluru", "Coimbatore", "Hyderabad", "Mumbai", "Delhi", "Pune", "Kolkata", "Kochi", "Ahmedabad"]
                    dest_idx = cities.index(edit_target["destination"]) if edit_target["destination"] in cities else 0
                    e_dest = st.selectbox("Destination", cities, index=dest_idx)

                with ec2:
                    curr_order_dt = parse_datetime(edit_target["order_date"])
                    e_o_date = st.date_input("Order Date", value=curr_order_dt.date())
                    e_o_time = st.time_input("Order Time", value=curr_order_dt.time())
                    e_proc = st.number_input("Processing Time (Mins)", min_value=5.0, max_value=720.0, value=float(edit_target["processing_time"]))
                    prio_idx = order_manager.VALID_PRIORITIES.index(edit_target["priority"]) if edit_target["priority"] in order_manager.VALID_PRIORITIES else 0
                    e_prio = st.selectbox("Shipment Priority", order_manager.VALID_PRIORITIES, index=prio_idx)

                with ec3:
                    curr_dl_dt = parse_datetime(edit_target["delivery_deadline"])
                    e_dl_date = st.date_input("Deadline Date", value=curr_dl_dt.date())
                    e_dl_time = st.time_input("Deadline Time", value=curr_dl_dt.time())
                    e_wt = st.number_input("Package Weight (kg)", min_value=0.1, value=float(edit_target["package_weight"]))
                    e_qty = st.number_input("Quantity", min_value=1, value=int(edit_target["package_quantity"]))
                    stat_idx = order_manager.VALID_STATUSES.index(edit_target["delivery_status"]) if edit_target["delivery_status"] in order_manager.VALID_STATUSES else 0
                    e_stat = st.selectbox("Delivery Status", order_manager.VALID_STATUSES, index=stat_idx)
                    e_veh = st.text_input("Assigned Vehicle", value=edit_target.get("assigned_vehicle", "Unassigned"))

                e_btn_col1, e_btn_col2 = st.columns([1, 1])
                with e_btn_col1:
                    save_edit = st.form_submit_button("💾 Save Changes", use_container_width=True)
                with e_btn_col2:
                    cancel_edit = st.form_submit_button("❌ Cancel", use_container_width=True)

                if save_edit:
                    e_full_order = datetime.combine(e_o_date, e_o_time)
                    e_full_dl = datetime.combine(e_dl_date, e_dl_time)

                    update_dict = {
                        "customer_name": e_cust.strip(),
                        "customer_location": e_loc.strip(),
                        "destination": e_dest.strip(),
                        "order_date": format_datetime(e_full_order, include_seconds=True),
                        "processing_time": float(e_proc),
                        "expected_delivery_date": format_datetime(e_full_dl - timedelta(hours=1), include_seconds=True),
                        "delivery_deadline": format_datetime(e_full_dl, include_seconds=True),
                        "priority": e_prio,
                        "package_weight": float(e_wt),
                        "package_quantity": int(e_qty),
                        "delivery_status": e_stat,
                        "assigned_vehicle": e_veh.strip() if e_veh else "Unassigned"
                    }
                    success, msg = order_manager.update_order(edit_target["order_id"], update_dict)
                    if success:
                        st.success(msg)
                        st.session_state["edit_order_id"] = None
                        st.rerun()
                    else:
                        st.error(msg)

                if cancel_edit:
                    st.session_state["edit_order_id"] = None
                    st.rerun()

    # 4. Delete Confirmation Card if an order was marked for deletion
    if st.session_state["delete_order_id"]:
        del_target = order_manager.get_order_by_id(st.session_state["delete_order_id"])
        if del_target:
            st.error(f"⚠️ **CONFIRM DELETION:** Are you sure you want to permanently delete order **{del_target['order_id']}** ({del_target['customer_name']})? This action cannot be undone.")
            d_col1, d_col2 = st.columns([1, 1])
            with d_col1:
                if st.button("🗑️ Yes, Delete Permanently", type="primary", use_container_width=True):
                    success, msg = order_manager.delete_order(del_target["order_id"])
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.session_state["delete_order_id"] = None
                    st.rerun()
            with d_col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state["delete_order_id"] = None
                    st.rerun()

    # 5. Search, Filter, and Sort Controls
    st.markdown("#### Registered Orders Directory")
    c_s1, c_s2, c_s3, c_s4, c_s5 = st.columns([2.0, 1.2, 1.2, 1.2, 1.4])
    with c_s1:
        search_query = st.text_input("🔍 Search", placeholder="Order ID, Customer, Destination...", label_visibility="collapsed")
    with c_s2:
        filter_priority = st.selectbox("Priority", ["All"] + order_manager.VALID_PRIORITIES, label_visibility="collapsed")
    with c_s3:
        filter_status = st.selectbox("Status", ["All"] + order_manager.VALID_STATUSES, label_visibility="collapsed")
    with c_s4:
        cities_filter = ["All", "Chennai", "Bengaluru", "Coimbatore", "Hyderabad", "Mumbai", "Delhi", "Pune", "Kolkata", "Kochi", "Ahmedabad"]
        filter_dest = st.selectbox("City", cities_filter, label_visibility="collapsed")
    with c_s5:
        sort_choice = st.selectbox("Sort", [
            ("deadline_asc", "Deadline (Earliest)"),
            ("deadline_desc", "Deadline (Latest)"),
            ("priority_desc", "Priority (High to Low)"),
            ("date_desc", "Order Date (Newest)"),
            ("order_id", "Order ID")
        ], format_func=lambda x: x[1], label_visibility="collapsed")

    # Fetch filtered and sorted orders
    orders_list = order_manager.get_orders(
        search=search_query,
        priority=filter_priority,
        status=filter_status,
        destination=filter_dest,
        sort_by=sort_choice[0]
    )

    st.write(f"Showing **{len(orders_list)}** order(s)")

    if not orders_list:
        st.info("No delivery orders match the current search or filter criteria. Click 'Load Demo Data' to populate sample orders.")
    else:
        # Render Professional Orders Table with Actions
        for ord_item in orders_list:
            prio = ord_item["priority"]
            stat = ord_item["delivery_status"]
            dl_str = ord_item["delivery_deadline"]
            dl_dt = parse_datetime(dl_str)
            now = datetime.now()

            # Deadline badge tag
            if stat in ["Delivered", "Cancelled"]:
                dl_badge = f"<span class='badge' style='background: rgba(148, 163, 184, 0.2); color: #94A3B8;'>Completed</span>"
            elif dl_dt < now:
                overdue_h = round((now - dl_dt).total_seconds() / 3600.0, 1)
                dl_badge = f"<span class='badge badge-critical'>OVERDUE ({overdue_h}h)</span>"
            elif (dl_dt - now).total_seconds() / 3600.0 <= 12.0:
                left_h = round((dl_dt - now).total_seconds() / 3600.0, 1)
                dl_badge = f"<span class='badge badge-high'>DUE IN {left_h}h</span>"
            else:
                dl_badge = f"<span class='badge' style='background: rgba(56, 189, 248, 0.15); color: #38BDF8;'>On Schedule</span>"

            # Priority CSS class
            prio_cls = f"badge-{prio.lower()}"
            # Status CSS class
            stat_slug = stat.lower().replace(" ", "")
            stat_cls = f"badge-{stat_slug}"

            # Table row layout
            row_col1, row_col2, row_col3, row_col4, row_col5, row_col6 = st.columns([1.2, 2.8, 1.8, 1.2, 1.4, 1.0])

            with row_col1:
                st.markdown(f"**`{ord_item['order_id']}`**")
                st.caption(f"{ord_item['assigned_vehicle']}")

            with row_col2:
                st.markdown(f"**{ord_item['customer_name']}**")
                st.caption(f"📍 {ord_item['customer_location']} → **{ord_item['destination']}**")

            with row_col3:
                st.markdown(f"⏱️ **{ord_item['processing_time']} min** prep")
                st.caption(f"📅 Deadline: {dl_str[:16]}")

            with row_col4:
                st.markdown(f"<span class='badge {prio_cls}'>{prio}</span>", unsafe_allow_html=True)
                st.markdown(f"<span class='badge {stat_cls}' style='margin-top: 4px;'>{stat}</span>", unsafe_allow_html=True)

            with row_col5:
                st.markdown(dl_badge, unsafe_allow_html=True)
                st.caption(f"📦 {ord_item['package_weight']}kg ({ord_item['package_quantity']} pcs)")

            with row_col6:
                btn_edit, btn_del = st.columns(2)
                with btn_edit:
                    if st.button("✏️", key=f"btn_edit_{ord_item['order_id']}", help="Edit order"):
                        st.session_state["edit_order_id"] = ord_item["order_id"]
                        st.session_state["delete_order_id"] = None
                        st.rerun()
                with btn_del:
                    if st.button("🗑️", key=f"btn_del_{ord_item['order_id']}", help="Delete order"):
                        st.session_state["delete_order_id"] = ord_item["order_id"]
                        st.session_state["edit_order_id"] = None
                        st.rerun()

            st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.05); margin: 8px 0;'>", unsafe_allow_html=True)


# =========================================================================
# MODULE 02 — DEADLINE-AWARE SCHEDULING OPTIMIZATION
# =========================================================================
elif st.session_state["selected_module"] == MOD_2:
    import scheduling_engine
    import plotly.express as px
    import plotly.graph_objects as go

    st.markdown("""
    <div class="section-header">
        <div>
            <h2 class="section-title">MODULE 02 — Deadline-Aware Scheduling Optimization</h2>
            <p style="color: #94A3B8; font-size: 0.88rem; margin: 4px 0 0 0;">
                Operations research scheduling engine with multi-vehicle resource dispatch and comparative algorithm benchmarking.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_single, tab_compare = st.tabs(["⚡ Single Algorithm Schedule Generator", "📊 3-Algorithm Comparative Benchmark"])

    # ----------------- TAB 1: SINGLE ALGORITHM GENERATOR -----------------
    with tab_single:
        st.markdown("#### Configure Dispatch & Scheduling Parameters")
        with st.form("form_schedule_params"):
            cfg_col1, cfg_col2, cfg_col3, cfg_col4 = st.columns([1.5, 1.2, 1.2, 1.5])

            with cfg_col1:
                sched_date = st.date_input("Scheduling Window Start Date", value=datetime.now().date())
                sched_time = st.time_input("Start Time", value=datetime.now().time())
                full_sched_start = datetime.combine(sched_date, sched_time)

            with cfg_col2:
                working_hours = st.selectbox("Working Shift Window", [8.0, 10.0, 12.0, 16.0, 24.0], index=2, format_func=lambda h: f"{int(h)} Hours Shift")
                num_vehicles = st.number_input("Available Delivery Vehicles (N)", min_value=1, max_value=10, value=2, step=1, help="Number of identical transport/dispatch resources")

            with cfg_col3:
                algo_choice = st.selectbox("Scheduling Strategy / Algorithm", [
                    "Deadline-Aware Priority Scheduling",
                    "Earliest Due Date (EDD)",
                    "First Come First Served (FCFS)"
                ], index=0)

                order_scope = st.selectbox("Orders Selection Criteria", [
                    "Pending Orders Only",
                    "Pending + Scheduled Orders",
                    "All Eligible Consignments"
                ], index=0)

            with cfg_col4:
                st.markdown("**Priority Weight Tuning** *(Score in [0-100])*")
                w_urgency = st.slider("Deadline Urgency Weight", 0.10, 0.60, 0.40, 0.05)
                w_prio = st.slider("Shipment Priority Weight", 0.10, 0.50, 0.30, 0.05)
                w_feas = st.slider("Processing Feasibility Weight", 0.10, 0.40, 0.20, 0.05)
                w_risk = round(max(0.0, 1.0 - (w_urgency + w_prio + w_feas)), 2)
                st.caption(f"Residual Delivery Risk Weight: **{w_risk:.2f}** (Total = 1.00)")

            btn_gen = st.form_submit_button("🚀 Generate & Save Schedule", use_container_width=True, type="primary")

        # Execute scheduling run
        if btn_gen:
            # Query eligible orders based on scope
            if order_scope == "Pending Orders Only":
                candidate_orders = order_manager.get_orders(status="Pending")
            elif order_scope == "Pending + Scheduled Orders":
                candidate_orders = order_manager.get_orders(status="Pending") + order_manager.get_orders(status="Scheduled")
            else:
                candidate_orders = [o for o in order_manager.get_orders(status="All") if o["delivery_status"] not in ["Delivered", "Cancelled"]]

            if not candidate_orders:
                st.warning("No eligible orders found matching the criteria. Only Pending and Scheduled orders can be scheduled.")
            else:
                weights_dict = {"urgency": w_urgency, "priority": w_prio, "feasibility": w_feas, "risk": w_risk}
                results, summary, run_id = scheduling_engine.generate_schedule(
                    orders=candidate_orders,
                    scheduling_start=full_sched_start,
                    num_resources=int(num_vehicles),
                    algorithm=algo_choice,
                    weights=weights_dict
                )
                st.session_state["active_schedule_results"] = results
                st.session_state["active_schedule_summary"] = summary
                st.session_state["active_run_id"] = run_id
                st.session_state["active_algo_choice"] = algo_choice
                st.session_state["active_num_vehicles"] = int(num_vehicles)
                st.session_state["active_start_time"] = format_datetime(full_sched_start)
                st.success(f"Schedule generated successfully! Created versioned execution run: **`{run_id}`**")

        # Display Active Schedule Results if available
        if "active_schedule_results" in st.session_state and st.session_state["active_schedule_results"]:
            sched_res = st.session_state["active_schedule_results"]
            sched_sum = st.session_state["active_schedule_summary"]
            run_id = st.session_state.get("active_run_id", "RUN-ACTIVE")
            algo_used = st.session_state.get("active_algo_choice", "Deadline-Aware Priority")
            v_used = st.session_state.get("active_num_vehicles", 1)

            st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;'>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h4 style="margin: 0; color: #F8FAFC;">Active Schedule Execution: <code style="color: #38BDF8;">{run_id}</code></h4>
                <div>
                    <span class="badge" style="background: rgba(56, 189, 248, 0.2); color: #38BDF8;">Strategy: {algo_used}</span>
                    <span class="badge" style="background: rgba(148, 163, 184, 0.2); color: #E2E8F0; margin-left: 8px;">Fleet: {v_used} Vehicles</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Metrics Row
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            with m_col1:
                st.metric("Total Scheduled", f"{sched_sum['total_orders']} Orders")
            with m_col2:
                st.metric("Predicted On-Time", f"{sched_sum['on_time_count']}", delta="Feasible")
            with m_col3:
                st.metric("Predicted Late", f"{sched_sum['late_count']}", delta="-Overdue/Late" if sched_sum['late_count'] > 0 else "0 Late", delta_color="inverse")
            with m_col4:
                feas_color = "normal" if sched_sum['on_time_feasibility_pct'] >= 80 else "off"
                st.metric("On-Time Feasibility", f"{sched_sum['on_time_feasibility_pct']}%")
            with m_col5:
                st.metric("Average Waiting", f"{sched_sum['avg_waiting_time_hours']} hrs")

            # Interactive Plotly Gantt Timeline
            fig_gantt = scheduling_engine.create_gantt_chart(sched_res)
            if fig_gantt:
                st.plotly_chart(fig_gantt, use_container_width=True)

            # Detailed Schedule Sequence Table
            st.markdown("##### Detailed Dispatch Sequence & Decision Log")
            for item in sched_res:
                status_label = item["deadline_status"]
                if status_label == "On-Time Feasible":
                    st_badge = "<span class='badge' style='background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981;'>On-Time Feasible</span>"
                elif status_label == "At-Risk":
                    st_badge = "<span class='badge' style='background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid #F59E0B;'>At-Risk</span>"
                elif status_label == "Predicted Late":
                    st_badge = "<span class='badge' style='background: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid #EF4444;'>Predicted Late</span>"
                else:
                    st_badge = "<span class='badge' style='background: rgba(220, 38, 38, 0.3); color: #FCA5A5; border: 1px solid #DC2626;'>Overdue</span>"

                prio_str = item["priority"]
                prio_badge = f"<span class='badge badge-{prio_str.lower()}'>{prio_str}</span>"

                r_c1, r_c2, r_c3, r_c4, r_c5 = st.columns([1.0, 2.8, 2.2, 1.8, 2.2])
                with r_c1:
                    st.markdown(f"**#{item['sequence_num']}** (`{item['order_id']}`)")
                    st.caption(f"🚛 {item['resource_id']}")
                with r_c2:
                    st.markdown(f"**{item['customer_name']}**")
                    st.caption(f"📍 Dest: **{item['destination']}** | Score: `{item['priority_score']:.1f}/100`")
                with r_c3:
                    st.markdown(f"Start: `{item['scheduled_start']}`")
                    st.caption(f"Done: `{item['expected_completion']}` ({item['processing_time_minutes']}m prep)")
                with r_c4:
                    st.markdown(f"{prio_badge} &nbsp; {st_badge}", unsafe_allow_html=True)
                    st.caption(f"Deadline: {item['delivery_deadline']}")
                with r_c5:
                    st.caption(f"💡 {item['decision_reason']}")

                st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.05); margin: 6px 0;'>", unsafe_allow_html=True)

    # ----------------- TAB 2: 3-ALGORITHM BENCHMARK -----------------
    with tab_compare:
        st.markdown("#### Multi-Algorithm Academic Benchmark (FCFS vs. EDD vs. Deadline-Aware Priority)")
        st.markdown("""
        Evaluates **First Come First Served (FCFS)**, **Earliest Due Date (EDD)**, and 
        **Deadline-Aware Priority Scheduling** on the exact same active consignments and vehicle constraints.
        """)

        comp_col1, comp_col2, comp_col3 = st.columns([1.5, 1.5, 1.2])
        with comp_col1:
            comp_start_date = st.date_input("Benchmark Start Date", value=datetime.now().date(), key="comp_start_d")
            comp_start_time = st.time_input("Benchmark Start Time", value=datetime.now().time(), key="comp_start_t")
            comp_full_start = datetime.combine(comp_start_date, comp_start_time)
        with comp_col2:
            comp_vehicles = st.number_input("Benchmark Fleet Size (Vehicles)", min_value=1, max_value=10, value=2, step=1, key="comp_v_num")
        with comp_col3:
            st.write("")
            st.write("")
            run_comparison_btn = st.button("⚖️ Run 3-Way Benchmark", use_container_width=True, type="primary")

        if run_comparison_btn:
            # Query eligible active orders
            candidate_orders = [o for o in order_manager.get_orders(status="All") if o["delivery_status"] not in ["Delivered", "Cancelled"]]

            if not candidate_orders:
                st.warning("No active orders available for comparison.")
            else:
                comp_results = scheduling_engine.compare_scheduling_algorithms(
                    orders=candidate_orders,
                    scheduling_start=comp_full_start,
                    num_resources=int(comp_vehicles)
                )
                st.session_state["comparison_benchmark"] = comp_results

        if "comparison_benchmark" in st.session_state:
            bench = st.session_state["comparison_benchmark"]

            st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 16px 0;'>", unsafe_allow_html=True)

            # Winner Banner (Honest, not hardcoded!)
            best_name = bench["best_algorithm"]
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
                <div style="font-size: 0.82rem; font-weight: 700; color: #34D399; text-transform: uppercase; letter-spacing: 0.05em;">Academic Benchmark Conclusion</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin: 4px 0;">Best Performing Strategy for this Dataset: <span style="color: #38BDF8;">{best_name}</span></div>
                <p style="color: #94A3B8; font-size: 0.88rem; margin: 0; line-height: 1.5;">
                    {" • ".join(bench["analysis_notes"]) if bench["analysis_notes"] else "All algorithms achieved comparable feasibility on this dataset."}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Comparison Table
            st.markdown("##### Comprehensive Performance Metrics Comparison")
            df_comp = pd.DataFrame(bench["comparison_table"])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

            # Plotly Comparative Bar Charts
            st.markdown("##### Visual Metrics Comparison")
            chart_col1, chart_col2 = st.columns(2)

            chart_data = []
            for item in bench["detailed_runs"].values():
                m = item["Metrics"]
                chart_data.append({
                    "Algorithm": item["Key"],
                    "On-Time Feasibility (%)": m["on_time_feasibility_pct"],
                    "Avg Tardiness (hrs)": m["avg_tardiness_hours"],
                    "Max Tardiness (hrs)": m["max_tardiness_hours"],
                    "Weighted Tardiness (hrs)": m["total_weighted_tardiness_hours"]
                })
            df_chart = pd.DataFrame(chart_data)

            with chart_col1:
                fig_feas = px.bar(
                    df_chart,
                    x="Algorithm",
                    y="On-Time Feasibility (%)",
                    color="Algorithm",
                    color_discrete_sequence=["#64748B", "#38BDF8", "#10B981"],
                    title="<b>On-Time Delivery Feasibility (%)</b>",
                    text_auto=True
                )
                fig_feas.update_layout(
                    plot_bgcolor="#111827",
                    paper_bgcolor="#1E293B",
                    font=dict(color="#E2E8F0"),
                    showlegend=False,
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_feas, use_container_width=True)

            with chart_col2:
                fig_tard = px.bar(
                    df_chart,
                    x="Algorithm",
                    y=["Avg Tardiness (hrs)", "Weighted Tardiness (hrs)"],
                    barmode="group",
                    title="<b>Lateness & Tardiness Comparison (Hours)</b>",
                    color_discrete_sequence=["#F59E0B", "#EF4444"]
                )
                fig_tard.update_layout(
                    plot_bgcolor="#111827",
                    paper_bgcolor="#1E293B",
                    font=dict(color="#E2E8F0"),
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_tard, use_container_width=True)


# =========================================================================
# MODULE 03 — DELIVERY PERFORMANCE EVALUATION
# =========================================================================
elif st.session_state["selected_module"] == MOD_3:
    import performance_evaluation

    st.markdown("""
    <div class="section-header">
        <div>
            <h2 class="section-title">MODULE 03 — Delivery Performance Evaluation</h2>
            <p style="color: #94A3B8; font-size: 0.88rem; margin: 4px 0 0 0;">
                Comprehensive analytics engine evaluating delivery punctuality, deadline compliance, and operational delay distributions from persistent database records.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Multi-Criteria Performance Filters
    st.markdown("#### Performance Analytics Filters")
    with st.container():
        f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([1.5, 1.2, 1.2, 1.2, 1.4])
        with f_c1:
            today = datetime.now().date()
            default_start = today - timedelta(days=7)
            perf_date_range = st.date_input("Delivery Date Range", value=(default_start, today + timedelta(days=2)), key="perf_date_range")
            if isinstance(perf_date_range, tuple) and len(perf_date_range) == 2:
                p_start_d, p_end_d = perf_date_range
            else:
                p_start_d, p_end_d = default_start, today + timedelta(days=2)

        with f_c2:
            perf_status = st.selectbox("Delivery Status", ["All", "Delivered", "Delayed", "Pending", "Scheduled", "In Transit", "Cancelled"], key="perf_status")
        with f_c3:
            perf_prio = st.selectbox("Shipment Priority", ["All", "Critical", "High", "Medium", "Low"], key="perf_prio")
        with f_c4:
            perf_dest = st.selectbox("Destination Hub", ["All", "Chennai", "Bengaluru", "Coimbatore", "Hyderabad", "Mumbai", "Delhi", "Pune", "Kolkata", "Kochi", "Ahmedabad"], key="perf_dest")
        with f_c5:
            perf_algo = st.selectbox("Scheduling Algorithm", ["All", "Deadline-Aware Priority", "Earliest Due Date (EDD)", "First Come First Served (FCFS)"], key="perf_algo")

    # Fetch and filter raw records
    raw_orders = database.get_orders(status_filter="All")
    raw_deliv_records = database.get_delivery_records()
    raw_schedules = database.get_latest_schedule(algorithm=None if perf_algo == "All" else perf_algo)
    raw_history = database.get_scheduling_history()

    # Apply filters to orders
    filtered_orders = []
    for o in raw_orders:
        if perf_status != "All" and o.get("delivery_status") != perf_status:
            continue
        if perf_prio != "All" and o.get("priority") != perf_prio:
            continue
        if perf_dest != "All" and o.get("destination") != perf_dest:
            continue
        o_date = parse_datetime(o.get("order_date")).date()
        if not (p_start_d <= o_date <= p_end_d):
            continue
        filtered_orders.append(o)

    # Apply filters to delivery records
    filtered_deliv = []
    for r in raw_deliv_records:
        if perf_status != "All" and r.get("delivery_status") != perf_status:
            continue
        if perf_prio != "All" and r.get("priority") != perf_prio:
            continue
        if perf_dest != "All" and r.get("destination") != perf_dest:
            continue
        r_dt = parse_datetime(r.get("actual_delivery_time")).date()
        if not (p_start_d <= r_dt <= p_end_d):
            continue
        filtered_deliv.append(r)

    # Calculate Formal KPIs
    perf_kpis = performance_evaluation.evaluate_delivery_performance(
        orders=filtered_orders,
        delivery_records=filtered_deliv,
        schedules=raw_schedules
    )

    st.write("")

    # 2. Performance KPI Cards Grid
    st.markdown("#### Primary Delivery Performance KPIs")
    pk_c1, pk_c2, pk_c3, pk_c4, pk_c5 = st.columns(5)
    with pk_c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Filtered Orders</div>
            <div class="kpi-value">{perf_kpis['total_orders']}</div>
            <div class="kpi-subtext">Active &amp; Historical</div>
        </div>
        """, unsafe_allow_html=True)

    with pk_c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Delivered Orders</div>
            <div class="kpi-value" style="color: #34D399;">{perf_kpis['total_completed_deliveries']}</div>
            <div class="kpi-subtext">{perf_kpis['delivered_orders']} on-time / {perf_kpis['delayed_orders']} late</div>
        </div>
        """, unsafe_allow_html=True)

    with pk_c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">On-Time Deliveries</div>
            <div class="kpi-value" style="color: #34D399;">{perf_kpis['delivered_orders']}</div>
            <div class="kpi-subtext">Met deadline constraint</div>
        </div>
        """, unsafe_allow_html=True)

    with pk_c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Late Deliveries</div>
            <div class="kpi-value" style="color: #F87171;">{perf_kpis['delayed_orders']}</div>
            <div class="kpi-subtext">Exceeded deadline</div>
        </div>
        """, unsafe_allow_html=True)

    with pk_c5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Pending / In-Transit</div>
            <div class="kpi-value" style="color: #FBBF24;">{perf_kpis['pending_orders'] + perf_kpis['in_transit_orders']}</div>
            <div class="kpi-subtext">{perf_kpis['pending_orders']} pending, {perf_kpis['in_transit_orders']} transit</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    pk2_c1, pk2_c2, pk2_c3, pk2_c4 = st.columns(4)
    with pk2_c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">On-Time Delivery Rate</div>
            <div class="kpi-value" style="color: #38BDF8;">{perf_kpis['on_time_delivery_rate']}%</div>
            <div class="kpi-subtext">Denominator: Total Delivered</div>
        </div>
        """, unsafe_allow_html=True)

    with pk2_c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Late Delivery Rate</div>
            <div class="kpi-value" style="color: #F87171;">{perf_kpis['late_delivery_rate']}%</div>
            <div class="kpi-subtext">Denominator: Total Delivered</div>
        </div>
        """, unsafe_allow_html=True)

    with pk2_c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Average Delivery Delay</div>
            <div class="kpi-value" style="color: #FB923C;">{perf_kpis['average_delivery_delay_hours']} hrs</div>
            <div class="kpi-subtext">Denominator: Late Deliveries Only</div>
        </div>
        """, unsafe_allow_html=True)

    with pk2_c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Average Waiting Time</div>
            <div class="kpi-value" style="color: #E2E8F0;">{perf_kpis['average_waiting_time_hours']} hrs</div>
            <div class="kpi-subtext">Denominator: Scheduled Jobs</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 3. Data-Backed Operational Insights Panel
    st.markdown("#### Operational Insights (Factual Findings)")
    insights_list = performance_evaluation.generate_performance_insights(
        kpi_metrics=perf_kpis,
        delivery_records=filtered_deliv,
        scheduling_history=raw_history
    )
    with st.container():
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 18px 24px; margin-bottom: 24px;">
        """, unsafe_allow_html=True)
        for insight_item in insights_list:
            st.markdown(f"🔹 **{insight_item}**")
        st.markdown("</div>", unsafe_allow_html=True)

    # 4. Six Plotly Performance Charts
    st.markdown("#### Interactive Performance Analytics Dashboards")

    chart_r1_c1, chart_r1_c2 = st.columns(2)
    with chart_r1_c1:
        fig_pie = performance_evaluation.chart_ontime_vs_late(filtered_deliv)
        st.plotly_chart(fig_pie, use_container_width=True)
    with chart_r1_c2:
        fig_bar_status = performance_evaluation.chart_status_distribution(filtered_orders)
        st.plotly_chart(fig_bar_status, use_container_width=True)

    chart_r2_c1, chart_r2_c2 = st.columns(2)
    with chart_r2_c1:
        fig_trend = performance_evaluation.chart_performance_over_time(filtered_deliv)
        st.plotly_chart(fig_trend, use_container_width=True)
    with chart_r2_c2:
        fig_algo = performance_evaluation.chart_algorithm_comparison(raw_history)
        st.plotly_chart(fig_algo, use_container_width=True)

    chart_r3_c1, chart_r3_c2 = st.columns(2)
    with chart_r3_c1:
        fig_delay_prio = performance_evaluation.chart_delay_by_priority(filtered_deliv)
        st.plotly_chart(fig_delay_prio, use_container_width=True)
    with chart_r3_c2:
        fig_daily = performance_evaluation.chart_daily_completions(filtered_deliv)
        st.plotly_chart(fig_daily, use_container_width=True)

    # 5. Delivery Records Table
    with st.expander("📋 View Actual Delivery Logs & Dispatch Audit Trail", expanded=False):
        if not filtered_deliv:
            st.info("No completed delivery records match current filter selections.")
        else:
            deliv_table_data = []
            for r in filtered_deliv:
                deliv_table_data.append({
                    "Order ID": r["order_id"],
                    "Customer": r.get("customer_name", "N/A"),
                    "Destination": r.get("destination", "N/A"),
                    "Priority": r.get("priority", "Medium"),
                    "Dispatched": str(r.get("actual_dispatch_time", ""))[:16],
                    "Delivered": str(r.get("actual_delivery_time", ""))[:16],
                    "Deadline": str(r.get("delivery_deadline", ""))[:16],
                    "Status": "On-Time" if int(r.get("on_time", 0)) == 1 else f"Late (+{r.get('delay_duration_hours')}h)",
                    "Notes": r.get("delivery_notes", "")
                })
            st.dataframe(pd.DataFrame(deliv_table_data), use_container_width=True, hide_index=True)


# ----------------- FOOTER & ACADEMIC PROJECT GUIDE -----------------
st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 36px 0 18px 0;'>", unsafe_allow_html=True)
with st.expander("📖 Academic Reference: Scheduling Formulas & Operations Research Foundations", expanded=False):
    ref_c1, ref_c2 = st.columns(2)
    with ref_c1:
        st.markdown("""
        ##### 📐 Deterministic Dispatch Time Model
        - $\\text{start} = \\max(\\text{resource\\_free\\_time}, \\text{arrival}, \\text{window\\_start})$
        - $\\text{completion} = \\text{start} + \\text{processing\\_time}$
        - $\\text{waiting} = \\max(0, \\text{start} - \\text{arrival})$
        - $\\text{tardiness} = \\max(0, \\text{completion} - \\text{deadline})$
        - $\\text{earliness} = \\max(0, \\text{deadline} - \\text{completion})$
        - $\\text{feasible} = \\text{completion} \\le \\text{deadline}$
        
        ##### ⚖️ Deadline-Aware Priority Formulation
        $$\\text{Score} = 0.40 \\cdot U + 0.30 \\cdot P + 0.20 \\cdot F + 0.10 \\cdot R$$
        - **$U$ (Urgency):** $1.0 - (\\text{Remaining} / \\text{Window})$, overdue = $1.0$
        - **$P$ (Priority):** Critical ($1.0$), High ($0.75$), Medium ($0.50$), Low ($0.25$)
        - **$F$ (Feasibility):** $\\text{Processing} / \\text{Remaining}$, measures deadline pressure
        - **$R$ (Risk):** Destination route complexity and package payload weight
        """)
    with ref_c2:
        st.markdown("""
        ##### 📊 Performance KPI Denominators
        - **On-Time Delivery Rate:** $(\\text{On-Time Delivered} / \\text{Total Completed}) \\times 100$
        - **Late Delivery Rate:** $(\\text{Late Delivered} / \\text{Total Completed}) \\times 100$
        - **Average Delivery Delay:** $\\sum \\text{Delay of Late Deliveries} / \\text{Count of Late Deliveries}$
        - **Average Waiting Time:** $\\sum \\text{Waiting Time} / \\text{Completed Scheduled Orders}$
        - **Average Tardiness:** $\\sum \\text{Positive Lateness} / \\text{Total Completed Deliveries}$
        - **Deadline Compliance:** $(\\text{Deliveries Within Deadline} / \\text{Total Completed}) \\times 100$
        
        *Note: Pending, Scheduled, and In Transit shipments are active operational states and are not treated as completed deliveries.*
        """)

st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.8rem; padding: 12px 0 24px 0;">
    <strong>Deadline-Aware Logistics Scheduling &amp; Delivery Performance Evaluation</strong><br>
    Academic Project Demonstration Platform • Python • Streamlit • SQLite • Plotly
</div>
""", unsafe_allow_html=True)


