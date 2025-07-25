import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from faker import Faker

# --------------------------
# CONFIGURATION (USER-EDITABLE)
# --------------------------
COMPANY_SIZE = "Enterprise"  # Options: Startup, SMB, Enterprise, Fortune500
FISCAL_YEAR_START = "January"  # Options: January, April, October
INDUSTRY = "Manufacturing"  # Options: Manufacturing, Retail, Healthcare
SIMULATE_STOCKOUTS = False
MULTI_CURRENCY = False

# --------------------------
# INITIALIZATION
# --------------------------
fake = Faker()
np.random.seed(42)
random.seed(42)

# Company Size Scaling
size_params = {
    "Startup": {"plants": 2, "materials": 200, "customers": 100},
    "SMB": {"plants": 3, "materials": 500, "customers": 500},
    "Enterprise": {"plants": 5, "materials": 1500, "customers": 5000},
    "Fortune500": {"plants": 10, "materials": 10000, "customers": 50000}
}

params = size_params[COMPANY_SIZE]

# --------------------------
# HELPER FUNCTIONS
# --------------------------
def generate_dates(start_date, end_date):
    """Generate business days only"""
    dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Weekdays
            dates.append(current)
        current += timedelta(days=1)
    return dates

def get_fiscal_period(date):
    """Dynamic fiscal period calculation"""
    if FISCAL_YEAR_START == "January":
        return date.month
    elif FISCAL_YEAR_START == "April":
        return (date.month - 3) % 12 or 12
    else:  # October
        return (date.month + 3) % 12 or 12

def apply_seasonality(date, base_value):
    """Apply seasonal adjustments"""
    month = date.month
    # Q4 Peak
    if month in [10, 11, 12]:
        return base_value * 1.3
    # Summer Slowdown
    elif month in [7, 8] and INDUSTRY == "Manufacturing":
        return base_value * 0.8
    # Retail Holiday Spike
    elif month == 12 and INDUSTRY == "Retail":
        return base_value * 1.5
    else:
        return base_value

# --------------------------
# DIMENSION TABLES
# --------------------------
print("Generating dimension tables...")

# Plant Dimension
plants = pd.DataFrame({
    "plant_id": range(1, params["plants"] + 1),
    "plant_name": [f"Plant {i}" for i in range(1, params["plants"] + 1)],
    "region": random.choices(["North", "South", "East", "West"], k=params["plants"]),
    "is_active": True
})

# Material Dimension
material_types = ["RAW", "SEMI", "FINISHED"]
product_groups = ["A", "B", "C", "D"]

materials = pd.DataFrame({
    "material_id": [f"MAT-{str(i).zfill(5)}" for i in range(1, params["materials"] + 1)],
    "material_name": [f"Material {i}" for i in range(1, params["materials"] + 1)],
    "material_type": random.choices(material_types, 
                                  weights=[0.5, 0.3, 0.2], 
                                  k=params["materials"]),
    "product_group": random.choices(product_groups, k=params["materials"]),
    "uom": "EA"
})

# Customer Dimension
customers = pd.DataFrame({
    "customer_id": [f"CUST-{str(i).zfill(5)}" for i in range(1, params["customers"] + 1)],
    "customer_name": [fake.company() for _ in range(params["customers"])],
    "customer_tier": random.choices(["A", "B", "C"], 
                                  weights=[0.2, 0.3, 0.5], 
                                  k=params["customers"]),
    "payment_terms": random.choices(["NET30", "NET45", "NET60"], 
                                   weights=[0.7, 0.2, 0.1], 
                                   k=params["customers"])
})

# Storage Locations
storage_locs = ["A001", "B001", "C001", "WH01", "WH02"]

# --------------------------
# MASTER DATA TABLES
# --------------------------
print("Generating master data tables...")

# Material Valuation (MBEW)
mbew = []
for _, mat in materials.iterrows():
    for plant_id in plants["plant_id"]:
        std_price = round(random.uniform(10, 500), 2)
        mbew.append({
            "material_id": mat["material_id"],
            "plant_id": plant_id,
            "valuation_area": "1000",
            "standard_price": std_price,
            "moving_avg_price": round(std_price * random.uniform(0.95, 1.05), 2),
            "price_unit": 1,
            "currency": "USD"
        })
mbew = pd.DataFrame(mbew)

# Initial Stock Levels (MARD)
mard = []
for _, mat in materials.iterrows():
    for plant_id in plants["plant_id"]:
        for loc in random.sample(storage_locs, k=2):  # 2 random locs per plant-material
            avg_demand = random.randint(100, 1000)
            mard.append({
                "material_id": mat["material_id"],
                "plant_id": plant_id,
                "storage_location": loc,
                "unrestricted_stock": avg_demand * 1.5,  # Initial stock
                "quality_insp": random.randint(0, 50),
                "blocked_stock": random.randint(0, 100) if SIMULATE_STOCKOUTS else 0,
                "safety_stock": round(avg_demand * 0.2),
                "last_count_date": None
            })
mard = pd.DataFrame(mard)

# --------------------------
# TRANSACTION GENERATION
# --------------------------
print("Generating transactional data...")

dates = generate_dates(datetime(2023, 1, 1), datetime(2024, 12, 31))
mseg_data = []
vbak_data = []
vbap_data = []
lips_data = []
vbfa_data = []

for date in dates:
    # Daily volume adjustments
    daily_factor = apply_seasonality(date, 1.0)
    
    # Goods Receipts (MSEG 101)
    gr_count = int(round(random.randint(10, 20) * daily_factor))
    for _ in range(gr_count):
        plant = random.choice(plants["plant_id"])
        mat = random.choice(materials["material_id"])
        std_price = mbew[(mbew["plant_id"] == plant) & 
                        (mbew["material_id"] == mat)]["standard_price"].values[0]
        
        # Manufacturing yield loss simulation
        ordered_qty = random.randint(50, 500)
        if INDUSTRY == "Manufacturing":
            received_qty = round(ordered_qty * random.uniform(0.9, 1.0))
        else:
            received_qty = ordered_qty
            
        mseg_data.append({
            "plant_id": plant,
            "material_id": mat,
            "movement_type": "101",
            "quantity": received_qty,
            "amount": received_qty * std_price,
            "document_date": date,
            "batch_number": f"BATCH-{date.strftime('%Y%m%d')}" if random.random() > 0.05 else None,
            "storage_location": random.choice(storage_locs) if random.random() > 0.03 else None,
            "fiscal_period": get_fiscal_period(date)
        })
    
    # Sales Orders (VBAK/VBAP)
    so_count = int(round(random.randint(15, 30) * daily_factor))
    for _ in range(so_count):
        order_id = f"OR{date.strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}"
        customer = random.choice(customers["customer_id"])
        
        vbak_data.append({
            "sales_order": order_id,
            "order_type": "OR",
            "sales_org": "1000",
            "distribution_channel": "10",
            "division": "00",
            "order_date": date,
            "customer_id": customer,
            "fiscal_period": get_fiscal_period(date)
        })
        
        # Order Items (1-5 per order)
        for item in range(1, random.randint(2, 6)):
            plant = random.choice(plants["plant_id"])
            mat = random.choice(materials["material_id"])
            std_price = mbew[(mbew["plant_id"] == plant) & 
                            (mbew["material_id"] == mat)]["standard_price"].values[0]
            qty = random.randint(1, 50)
            price = std_price * 1.2  # 20% margin
            
            vbap_data.append({
                "sales_order": order_id,
                "sales_order_item": item,
                "material_id": mat,
                "order_quantity": qty,
                "plant_id": plant,
                "net_value": qty * price,
                "currency": "USD"
            })
            
            # Delivery Processing (LIPS)
            delivery_status = random.choices(
                ["A", "B", "C"], 
                weights=[0.8, 0.15, 0.05]
            )[0]
            
            if delivery_status == "A":  # Complete
                delivery_qty = qty
            elif delivery_status == "B":  # Partial
                # Only allow partial if qty > 1, else treat as backorder
                if qty > 1:
                    delivery_qty = random.randint(1, qty - 1)
                else:
                    delivery_qty = 0
            else:  # Backorder
                delivery_qty = 0
                
            delivery_id = f"DL{date.strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}"
            lips_data.append({
                "delivery_id": delivery_id,
                "delivery_item": item,
                "material_id": mat,
                "plant_id": plant,
                "delivery_quantity": delivery_qty,
                "delivery_status": delivery_status,
                "delivery_date": date + timedelta(days=random.randint(1, 3)),
                "sales_order": order_id,
                "sales_order_item": item,
                "fiscal_period": get_fiscal_period(date)
            })
            
            # Goods Issue for Delivery (MSEG 261)
            if delivery_qty > 0:
                mseg_data.append({
                    "plant_id": plant,
                    "material_id": mat,
                    "movement_type": "261",
                    "quantity": -delivery_qty,
                    "amount": -delivery_qty * std_price,
                    "document_date": date + timedelta(days=random.randint(1, 3)),
                    "batch_number": None,
                    "storage_location": random.choice(storage_locs),
                    "fiscal_period": get_fiscal_period(date)
                })
            
            # Document Flow (VBFA)
            vbfa_data.append({
                "preceding_doc": order_id,
                "preceding_item": item,
                "subsequent_doc": delivery_id,
                "subsequent_item": item,
                "document_category": "C",
                "quantity": qty,
                "date": date
            })
            
            # Backorder Creation if applicable
            if delivery_status in ["B", "C"]:
                backorder_qty = qty - delivery_qty
                vbfa_data.append({
                    "preceding_doc": delivery_id,
                    "preceding_item": item,
                    "subsequent_doc": f"BO{delivery_id}",
                    "subsequent_item": item,
                    "document_category": "N",
                    "quantity": backorder_qty,
                    "date": date + timedelta(days=1)
                })

# Create DataFrames
mseg = pd.DataFrame(mseg_data)
vbak = pd.DataFrame(vbak_data)
vbap = pd.DataFrame(vbap_data)
lips = pd.DataFrame(lips_data)
vbfa = pd.DataFrame(vbfa_data)

# --------------------------
# STOCK LEVEL UPDATES
# --------------------------
print("Updating stock levels...")

# Simulate daily stock changes
for _, row in mseg.iterrows():
    plant = row["plant_id"]
    mat = row["material_id"]
    loc = row["storage_location"]
    qty = row["quantity"]
    
    mask = ((mard["plant_id"] == plant) & 
            (mard["material_id"] == mat) & 
            (mard["storage_location"] == loc))
    
    if not mard[mask].empty:
        mard.loc[mask, "unrestricted_stock"] += qty

# --------------------------
# DATA QUALITY CHECKS
# --------------------------
print("Running data quality checks...")

# 1. Negative Stock Simulation (if enabled)
if SIMULATE_STOCKOUTS:
    for _, row in mard.iterrows():
        if row["unrestricted_stock"] < 0:
            mard.loc[_, "blocked_stock"] += abs(row["unrestricted_stock"])
            mard.loc[_, "unrestricted_stock"] = 0

# 2. Add random data issues
def introduce_data_issues(df, col, issue_rate, issue_type="null"):
    """Introduce controlled data quality issues"""
    idx = df.sample(frac=issue_rate).index
    if issue_type == "null":
        df.loc[idx, col] = None
    elif issue_type == "zero":
        df.loc[idx, col] = 0
    return df

mseg = introduce_data_issues(mseg, "batch_number", 0.05)
mseg = introduce_data_issues(mseg, "storage_location", 0.03)
lips = introduce_data_issues(lips, "delivery_quantity", 0.02, "zero")

# --------------------------
# EXPORT TO CSV
# --------------------------
print("Exporting to CSV...")

# Dimension Tables
plants.to_csv("dim_plants.csv", index=False)
materials.to_csv("dim_materials.csv", index=False)
customers.to_csv("dim_customers.csv", index=False)

# Master Data Tables
mbew.to_csv("mbew_valuation.csv", index=False)
mard.to_csv("mard_stock.csv", index=False)

# Transaction Tables
mseg.to_csv("mseg_movements.csv", index=False)
vbak.to_csv("vbak_sales_orders.csv", index=False)
vbap.to_csv("vbap_sales_items.csv", index=False)
lips.to_csv("lips_deliveries.csv", index=False)
vbfa.to_csv("vbfa_document_flow.csv", index=False)

# --------------------------
# VALIDATION REPORT
# --------------------------
print("\nData Generation Complete!")
print(f"\n=== Dataset Summary ({COMPANY_SIZE} Size) ===")
print(f"Plants: {len(plants)}")
print(f"Materials: {len(materials)}")
print(f"Customers: {len(customers)}")
print(f"Date Range: {dates[0].date()} to {dates[-1].date()}")
print(f"\n=== Transaction Volumes ===")
print(f"Goods Movements (MSEG): {len(mseg):,}")
print(f"Sales Orders (VBAK): {len(vbak):,}")
print(f"Deliveries (LIPS): {len(lips):,}")
print(f"Document Flows (VBFA): {len(vbfa):,}")

# Calculate sample KPIs
sample_cogs = mseg[mseg["movement_type"] == "261"]["amount"].abs().sum()
avg_inv = (mard["unrestricted_stock"] * mard.merge(mbew, on=["plant_id", "material_id"])["standard_price"]).mean()
turnover = sample_cogs / avg_inv

complete_deliveries = len(lips[lips["delivery_status"] == "A"])
fill_rate = complete_deliveries / len(vbak)

print(f"\n=== Sample KPIs ===")
print(f"Inventory Turnover: {turnover:.1f} (Target: 4-6)")
print(f"Fill Rate: {fill_rate:.1%} (Target: 85-95%)")
print(f"Backorder Rate: {(len(lips) - complete_deliveries)/len(vbak):.1%} (Target: 3-7%)")

print("\nCSV files exported successfully!")