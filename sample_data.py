"""
Sample Demonstration Logistics Dataset
---------------------------------------
Realistic Indian logistics delivery dataset spanning major commercial hubs:
Chennai, Bengaluru, Coimbatore, Hyderabad, Mumbai, Delhi, Pune, Kolkata, Kochi, Ahmedabad.

Adheres strictly to the official Time Model:
- processing_time: preparation/dispatch duration in minutes (e.g. 45 min, 60 min, 120 min)
- Deadlines and arrivals properly formatted
- Historical completed records (on-time and delayed) pre-populated for Module 03 evaluation
- Clearly designated as demonstration data
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from database import add_order, record_delivery_completion, get_connection


# 25 Realistic Demonstration Orders across Indian Hubs
SAMPLE_ORDERS = [
    # --- HISTORICAL DELIVERED ORDERS (Both On-Time and Delayed for Module 3 Analytics) ---
    {
        "order_id": "ORD-1001",
        "customer_name": "Apollo Hospitals Central Pharmacy",
        "customer_location": "Greams Road Hub, Chennai",
        "destination": "Coimbatore",
        "order_offset_hours": -48,
        "processing_time": 90.0,       # 90 minutes dispatch prep
        "deadline_offset_hours": -24,
        "priority": "Critical",
        "package_weight": 14.5,
        "package_quantity": 8,
        "delivery_status": "Delivered",
        "assigned_vehicle": "Express Van-01",
        "actual_delivered_offset_hours": -26,  # Delivered 2 hrs before deadline -> On-Time
        "notes": "Emergency cold-chain vaccine consignment delivered successfully."
    },
    {
        "order_id": "ORD-1002",
        "customer_name": "Tata Croma Electronics DC",
        "customer_location": "Bhiwandi Hub, Mumbai",
        "destination": "Pune",
        "order_offset_hours": -52,
        "processing_time": 120.0,      # 120 minutes dispatch prep
        "deadline_offset_hours": -28,
        "priority": "High",
        "package_weight": 85.0,
        "package_quantity": 25,
        "delivery_status": "Delivered",
        "assigned_vehicle": "Medium Truck-02",
        "actual_delivered_offset_hours": -30,  # On-Time
        "notes": "Delivered ahead of expected schedule at Pune DC."
    },
    {
        "order_id": "ORD-1003",
        "customer_name": "Reliance Retail Wholesale",
        "customer_location": "Whitefield Logistics Yard, Bengaluru",
        "destination": "Chennai",
        "order_offset_hours": -42,
        "processing_time": 180.0,      # 180 minutes dispatch prep
        "deadline_offset_hours": -18,
        "priority": "Medium",
        "package_weight": 140.0,
        "package_quantity": 40,
        "delivery_status": "Delayed",
        "assigned_vehicle": "Heavy Freight-01",
        "actual_delivered_offset_hours": -14,  # Delivered 4 hrs late -> Delayed
        "notes": "Delayed due to national highway toll congestion near Ranipet."
    },
    {
        "order_id": "ORD-1004",
        "customer_name": "Sun Pharma Lifesciences",
        "customer_location": "Peenya Industrial Area, Bengaluru",
        "destination": "Hyderabad",
        "order_offset_hours": -36,
        "processing_time": 75.0,       # 75 minutes dispatch prep
        "deadline_offset_hours": -12,
        "priority": "Critical",
        "package_weight": 22.0,
        "package_quantity": 12,
        "delivery_status": "Delivered",
        "assigned_vehicle": "Express Van-02",
        "actual_delivered_offset_hours": -15,  # On-Time
        "notes": "Delivered directly to hospital cold-storage bay."
    },
    {
        "order_id": "ORD-1005",
        "customer_name": "Havells India Electricals",
        "customer_location": "Okhla Industrial Phase-III, Delhi",
        "destination": "Mumbai",
        "order_offset_hours": -60,
        "processing_time": 240.0,      # 240 minutes dispatch prep
        "deadline_offset_hours": -20,
        "priority": "Low",
        "package_weight": 310.0,
        "package_quantity": 65,
        "delivery_status": "Delayed",
        "assigned_vehicle": "Multi-Axle Truck-01",
        "actual_delivered_offset_hours": -15,  # Delivered 5 hrs late -> Delayed
        "notes": "Detained at interstate commercial inspection checkpost."
    },
    {
        "order_id": "ORD-1006",
        "customer_name": "Flipkart Fulfillment Center",
        "customer_location": "Kompally Hub, Hyderabad",
        "destination": "Bengaluru",
        "order_offset_hours": -30,
        "processing_time": 60.0,       # 60 minutes dispatch prep
        "deadline_offset_hours": -8,
        "priority": "High",
        "package_weight": 45.0,
        "package_quantity": 18,
        "delivery_status": "Delivered",
        "assigned_vehicle": "Express Cargo-03",
        "actual_delivered_offset_hours": -10,  # On-Time
        "notes": "Consumer electronic batch delivered in prime condition."
    },
    {
        "order_id": "ORD-1007",
        "customer_name": "Titan Precision Engineering",
        "customer_location": "Hosur Industrial Complex, Tamil Nadu",
        "destination": "Chennai",
        "order_offset_hours": -26,
        "processing_time": 45.0,       # 45 minutes dispatch prep
        "deadline_offset_hours": -6,
        "priority": "High",
        "package_weight": 18.5,
        "package_quantity": 10,
        "delivery_status": "Delivered",
        "assigned_vehicle": "Courier Van-04",
        "actual_delivered_offset_hours": -7,  # On-Time
        "notes": "Delivered to Guindy industrial tech center."
    },
    {
        "order_id": "ORD-1008",
        "customer_name": "Ashok Leyland Spare Logistics",
        "customer_location": "Ennore Assembly Yard, Chennai",
        "destination": "Coimbatore",
        "order_offset_hours": -28,
        "processing_time": 150.0,      # 150 minutes dispatch prep
        "deadline_offset_hours": -4,
        "priority": "Medium",
        "package_weight": 190.0,
        "package_quantity": 30,
        "delivery_status": "Delayed",
        "assigned_vehicle": "Heavy Freight-02",
        "actual_delivered_offset_hours": -1,  # Delivered 3 hrs late -> Delayed
        "notes": "Engine component shipment delayed by minor vehicle maintenance en route."
    },
    {
        "order_id": "ORD-1009",
        "customer_name": "Zydus Healthcare Laboratories",
        "customer_location": "Changodar GIDC, Ahmedabad",
        "destination": "Mumbai",
        "order_offset_hours": -24,
        "processing_time": 60.0,       # 60 minutes dispatch prep
        "deadline_offset_hours": -2,
        "priority": "Critical",
        "package_weight": 35.0,
        "package_quantity": 15,
        "delivery_status": "Delivered",
        "assigned_vehicle": "Express Van-01",
        "actual_delivered_offset_hours": -4,  # On-Time
        "notes": "Medical diagnostic consumables delivered safely."
    },

    # --- IN-TRANSIT & SCHEDULED ACTIVE ORDERS ---
    {
        "order_id": "ORD-1010",
        "customer_name": "Amazon Sortation Hub",
        "customer_location": "Shamshabad Cargo Airport, Hyderabad",
        "destination": "Chennai",
        "order_offset_hours": -12,
        "processing_time": 90.0,
        "deadline_offset_hours": 6,
        "priority": "High",
        "package_weight": 52.0,
        "package_quantity": 20,
        "delivery_status": "In Transit",
        "assigned_vehicle": "Express Van-02",
        "actual_delivered_offset_hours": None,
        "notes": "Currently en route on NH16 corridor."
    },
    {
        "order_id": "ORD-1011",
        "customer_name": "Mahindra Aerospace Components",
        "customer_location": "Chakan MIDC Phase-II, Pune",
        "destination": "Bengaluru",
        "order_offset_hours": -10,
        "processing_time": 180.0,
        "deadline_offset_hours": 8,
        "priority": "Critical",
        "package_weight": 95.0,
        "package_quantity": 14,
        "delivery_status": "In Transit",
        "assigned_vehicle": "Secured Freight-01",
        "actual_delivered_offset_hours": None,
        "notes": "High priority aerospace parts under GPS-tracked transit."
    },
    {
        "order_id": "ORD-1012",
        "customer_name": "Larsen & Toubro Electrical Hub",
        "customer_location": "Manapakkam Campus, Chennai",
        "destination": "Kochi",
        "order_offset_hours": -8,
        "processing_time": 120.0,
        "deadline_offset_hours": 12,
        "priority": "Medium",
        "package_weight": 110.0,
        "package_quantity": 22,
        "delivery_status": "Scheduled",
        "assigned_vehicle": "Medium Truck-01",
        "actual_delivered_offset_hours": None,
        "notes": "Assigned to evening interstate departure slot."
    },

    # --- PENDING ORDERS AVAILABLE FOR SCHEDULING OPTIMIZATION ---
    {
        "order_id": "ORD-1013",
        "customer_name": "Biocon Life Sciences Bio-Park",
        "customer_location": "Electronic City Phase-I, Bengaluru",
        "destination": "Chennai",
        "order_offset_hours": -5,
        "processing_time": 45.0,       # 45 minutes
        "deadline_offset_hours": 4,    # URGENT DEADLINE (Critical)
        "priority": "Critical",
        "package_weight": 28.0,
        "package_quantity": 10,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Temperature-controlled biological culture samples."
    },
    {
        "order_id": "ORD-1014",
        "customer_name": "Bosch Automotive Systems",
        "customer_location": "Adugodi Tech Center, Bengaluru",
        "destination": "Coimbatore",
        "order_offset_hours": -6,
        "processing_time": 60.0,       # 60 minutes
        "deadline_offset_hours": 10,
        "priority": "High",
        "package_weight": 65.0,
        "package_quantity": 18,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "ECU sensor modules for automotive assembly."
    },
    {
        "order_id": "ORD-1015",
        "customer_name": "Godrej Interio Logistics",
        "customer_location": "Vikhroli Mega Depot, Mumbai",
        "destination": "Ahmedabad",
        "order_offset_hours": -4,
        "processing_time": 120.0,      # 120 minutes
        "deadline_offset_hours": 20,
        "priority": "Medium",
        "package_weight": 240.0,
        "package_quantity": 35,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Commercial modular office fixtures."
    },
    {
        "order_id": "ORD-1016",
        "customer_name": "Serum Institute Supply Division",
        "customer_location": "Hadapsar Plant, Pune",
        "destination": "Delhi",
        "order_offset_hours": -3,
        "processing_time": 90.0,       # 90 minutes
        "deadline_offset_hours": 6,    # TIGHT DEADLINE (Critical)
        "priority": "Critical",
        "package_weight": 42.0,
        "package_quantity": 16,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Critical immunization supply batch."
    },
    {
        "order_id": "ORD-1017",
        "customer_name": "ITC Agro & Consumer Goods",
        "customer_location": "Rajarhat Industrial Park, Kolkata",
        "destination": "Hyderabad",
        "order_offset_hours": -7,
        "processing_time": 180.0,      # 180 minutes
        "deadline_offset_hours": 28,
        "priority": "Low",
        "package_weight": 380.0,
        "package_quantity": 80,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Non-perishable packaged consumer cargo."
    },
    {
        "order_id": "ORD-1018",
        "customer_name": "Tata Motors Spare Parts Hub",
        "customer_location": "Pimpri Foundry Zone, Pune",
        "destination": "Mumbai",
        "order_offset_hours": -2,
        "processing_time": 45.0,       # 45 minutes
        "deadline_offset_hours": 8,
        "priority": "High",
        "package_weight": 70.0,
        "package_quantity": 15,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Urgent breakdown replacement clutch assemblies."
    },
    {
        "order_id": "ORD-1019",
        "customer_name": "Schneider Electric Solutions",
        "customer_location": "Attibele Industrial Area, Bengaluru",
        "destination": "Hyderabad",
        "order_offset_hours": -4,
        "processing_time": 75.0,       # 75 minutes
        "deadline_offset_hours": 14,
        "priority": "Medium",
        "package_weight": 88.0,
        "package_quantity": 24,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Industrial breaker units for substation retrofit."
    },
    {
        "order_id": "ORD-1020",
        "customer_name": "Dr. Reddy's Chemical Laboratories",
        "customer_location": "Bollaram Industrial Area, Hyderabad",
        "destination": "Bengaluru",
        "order_offset_hours": -1,
        "processing_time": 60.0,       # 60 minutes
        "deadline_offset_hours": 5,    # Critical deadline
        "priority": "Critical",
        "package_weight": 30.0,
        "package_quantity": 12,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Urgent clinical trial medication packs."
    },
    {
        "order_id": "ORD-1021",
        "customer_name": "Asian Paints Central Depot",
        "customer_location": "Sriperumbudur SIPCOT, Chennai",
        "destination": "Coimbatore",
        "order_offset_hours": -8,
        "processing_time": 90.0,       # 90 minutes
        "deadline_offset_hours": 18,
        "priority": "Medium",
        "package_weight": 210.0,
        "package_quantity": 50,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Architectural primer paint canisters."
    },
    {
        "order_id": "ORD-1022",
        "customer_name": "Wipro GE Healthcare Systems",
        "customer_location": "Whitefield Export Zone, Bengaluru",
        "destination": "Kochi",
        "order_offset_hours": -3,
        "processing_time": 105.0,      # 105 minutes
        "deadline_offset_hours": 12,
        "priority": "High",
        "package_weight": 55.0,
        "package_quantity": 6,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Ultrasound transducer probes and diagnostic cables."
    },
    {
        "order_id": "ORD-1023",
        "customer_name": "Sundaram Fasteners Automotive",
        "customer_location": "Padi Industrial Estate, Chennai",
        "destination": "Pune",
        "order_offset_hours": -9,
        "processing_time": 150.0,      # 150 minutes
        "deadline_offset_hours": 32,
        "priority": "Low",
        "package_weight": 420.0,
        "package_quantity": 90,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Standard high-tensile fasteners and brackets."
    },
    {
        "order_id": "ORD-1024",
        "customer_name": "Cipla Distribution Center",
        "customer_location": "Kurkumbh MIDC, Pune",
        "destination": "Hyderabad",
        "order_offset_hours": -2,
        "processing_time": 75.0,       # 75 minutes
        "deadline_offset_hours": 11,
        "priority": "High",
        "package_weight": 38.0,
        "package_quantity": 14,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Inhalation therapy supplies for hospital network."
    },
    {
        "order_id": "ORD-1025",
        "customer_name": "Lupin Pharma Express Hub",
        "customer_location": "Tarapur Industrial Area, Mumbai",
        "destination": "Delhi",
        "order_offset_hours": -1,
        "processing_time": 120.0,      # 120 minutes
        "deadline_offset_hours": 16,
        "priority": "Critical",
        "package_weight": 45.0,
        "package_quantity": 18,
        "delivery_status": "Pending",
        "assigned_vehicle": "Unassigned",
        "actual_delivered_offset_hours": None,
        "notes": "Sensitive cardiovascular formulations with strict deadline."
    }
]


def seed_demonstration_data(force: bool = False) -> int:
    """
    Seed realistic demonstration data into SQLite database.
    If data already exists and force is False, skips insertion to avoid duplication.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    existing_count = cursor.fetchone()["count"]
    conn.close()

    if existing_count > 0 and not force:
        return existing_count

    if force:
        from database import reset_database
        reset_database()

    base_time = datetime.now()
    inserted = 0

    for item in SAMPLE_ORDERS:
        order_dt = base_time + timedelta(hours=item["order_offset_hours"])
        deadline_dt = base_time + timedelta(hours=item["deadline_offset_hours"])
        expected_dt = deadline_dt - timedelta(hours=1)

        order_record = {
            "order_id": item["order_id"],
            "customer_name": item["customer_name"],
            "customer_location": item["customer_location"],
            "destination": item["destination"],
            "order_date": order_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_time": float(item["processing_time"]),
            "expected_delivery_date": expected_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "delivery_deadline": deadline_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "priority": item["priority"],
            "package_weight": item["package_weight"],
            "package_quantity": item["package_quantity"],
            "delivery_status": item["delivery_status"],
            "assigned_vehicle": item["assigned_vehicle"],
            "created_at": order_dt.strftime("%Y-%m-%d %H:%M:%S")
        }

        success = add_order(order_record)
        if success:
            inserted += 1

            # If order has historical completion, log in delivery_records
            if item["actual_delivered_offset_hours"] is not None:
                dispatch_dt = order_dt + timedelta(hours=1.5)
                delivery_dt = base_time + timedelta(hours=item["actual_delivered_offset_hours"])
                record_delivery_completion(
                    order_id=item["order_id"],
                    actual_dispatch_time=dispatch_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    actual_delivery_time=delivery_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    notes=item["notes"]
                )

    return inserted
