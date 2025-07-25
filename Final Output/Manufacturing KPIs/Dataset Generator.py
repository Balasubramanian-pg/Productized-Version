import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
from faker import Faker

# --- Configuration Parameters ---
START_DATE = datetime(2023, 4, 1) # Fiscal year starts April 1st
END_DATE = datetime(2025, 3, 31) # 2 years historical data
OUTPUT_DIR = "manufacturing_coo_demo_data"
NUM_PLANTS = 3 # Enterprise scale: 3 distinct plants
NUM_MATERIALS = 750 # Enterprise scale: 500-1000 products
NUM_EMPLOYEES = 750 # Enterprise scale: 500-1000 employees
NUM_WORK_CENTERS_PER_PLANT = 30 # 20-50 per plant
NUM_EQUIPMENT_PER_WORK_CENTER = 10 # 5-15 per WC
NUM_VENDORS = 75 # 50-100 vendors

# --- Ensure output directory exists ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Initialize Faker for realistic data ---
fake = Faker('en_IN') # Using Indian locale for names, cities etc. given current location context

# --- Helper Functions ---
def save_dataframe_to_csv(df, filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(filepath, index=False)
    print(f"Saved {filename} with {len(df)} rows.")

def get_random_date_in_range(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

# --- 1. Dim_Date Generation ---
def generate_dim_date(start_date, end_date):
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        fiscal_year = current_date.year if current_date.month >= 4 else current_date.year - 1
        fiscal_period = (current_date.month - 4) % 12 + 1 # April = 1, May = 2, ..., March = 12

        date_list.append({
            'Date_ID': current_date.strftime('%Y-%m-%d'),
            'Day_Of_Week': current_date.strftime('%A'),
            'Day_Name': current_date.strftime('%a'),
            'Month_Of_Year': current_date.month,
            'Month_Name': current_date.strftime('%B'),
            'Quarter': (current_date.month - 1) // 3 + 1,
            'Year': current_date.year,
            'Fiscal_Period': fiscal_period,
            'Fiscal_Year': fiscal_year,
            'Is_Weekend': 1 if current_date.weekday() >= 5 else 0, # Saturday=5, Sunday=6
            'Is_Holiday': 0 # Will be populated later if specific holidays are needed, keeping simple for now
        })
        current_date += timedelta(days=1)
    df = pd.DataFrame(date_list)
    return df

# --- 2. Dim_Plant Generation ---
def generate_dim_plant(num_plants):
    plants = []
    plant_names = ["Springfield Operations", "Delta Manufacturing", "Apex Production", "Global Fab", "East Coast Assembly"]
    cities = ["Coimbatore", "Pune", "Bengaluru", "Chennai", "Delhi", "Hyderabad", "Mumbai", "Ahmedabad", "Kolkata", "Jaipur"]
    countries = ["India", "USA", "Germany", "China", "Mexico"] # Diversify countries
    regions = ["South Asia", "North America", "Europe", "East Asia", "Latin America"]

    for i in range(num_plants):
        plant_id = f"PLNT{i+1}"
        # Ensure diverse locations for demo purposes
        city = fake.city()
        country = random.choice(countries)
        if country == "India": region = "South Asia"
        elif country == "USA": region = "North America"
        elif country == "Germany": region = "Europe"
        elif country == "China": region = "East Asia"
        else: region = "Latin America"

        plants.append({
            'Plant_ID': plant_id,
            'Plant_Name': random.choice(plant_names),
            'City': city,
            'Country': country,
            'Region': region
        })
    return pd.DataFrame(plants)

# --- 3. Dim_Material Generation ---
def generate_dim_material(num_materials):
    materials = []
    material_types = ['Raw Material', 'Semi-Finished Goods', 'Finished Goods', 'Packaging']
    units = ['EA', 'KG', 'M', 'LBS', 'LIT', 'PCS']
    product_hierarchies = {
        'Finished Goods': ['Electronics.TVs.SmartTV', 'Electronics.Audio.Speakers', 'Apparel.Tops.T-Shirts', 'HomeGoods.Furniture.Chairs'],
        'Semi-Finished Goods': ['Electronics.Components.Chipsets', 'Apparel.Fabric.CottonRolls', 'HomeGoods.Wood.Panels'],
        'Raw Material': ['Metal.Aluminum', 'Plastic.Pellets', 'Cotton.Fiber'],
        'Packaging': ['Box.Cardboard', 'Film.Plastic']
    }

    for i in range(num_materials):
        material_id = f"MAT{str(i+1).zfill(5)}"
        material_type = random.choice(material_types)
        material_name = fake.word().capitalize() + " " + fake.word().capitalize() + (" Assembly" if "Semi" in material_type else "") + (" Finished Product" if "Finished" in material_type else "")
        base_unit = random.choice(units)
        hierarchy = random.choice(product_hierarchies.get(material_type, ['General.Miscellaneous']))

        materials.append({
            'Material_ID': material_id,
            'Material_Name': material_name,
            'Material_Type': material_type,
            'Base_Unit_Of_Measure': base_unit,
            'Product_Hierarchy': hierarchy
        })
    return pd.DataFrame(materials)

# --- 4. Dim_Employee Generation ---
def generate_dim_employee(num_employees):
    employees = []
    departments = ['Production', 'Quality', 'Maintenance', 'Logistics', 'Operations Management', 'Safety', 'HR']
    job_titles = {
        'Production': ['Operator', 'Team Lead', 'Supervisor', 'Production Manager'],
        'Quality': ['QA Inspector', 'Quality Engineer', 'Quality Manager'],
        'Maintenance': ['Technician', 'Maintenance Engineer', 'Maintenance Supervisor'],
        'Logistics': ['Warehouse Associate', 'Logistics Coordinator'],
        'Operations Management': ['Plant Manager', 'Operations Director'],
        'Safety': ['Safety Officer'],
        'HR': ['HR Business Partner']
    }

    for i in range(num_employees):
        employee_id = f"EMP{str(i+1).zfill(4)}"
        employee_name = fake.name()
        department = random.choice(departments)
        job_title = random.choice(job_titles.get(department, ['Specialist']))
        hire_date = get_random_date_in_range(START_DATE - timedelta(days=365*5), START_DATE) # Hired up to 5 years before start date

        employees.append({
            'Employee_ID': employee_id,
            'Employee_Name': employee_name,
            'Department': department,
            'Job_Title': job_title,
            'Hire_Date': hire_date.strftime('%Y-%m-%d')
        })
    return pd.DataFrame(employees)

# --- 5. Dim_Work_Center Generation ---
def generate_dim_work_center(df_plants, num_work_centers_per_plant, df_employees):
    work_centers = []
    usage_types = ['1'] # '1' for Production
    capacity_categories = ['Machine', 'Labor', 'Assembly']
    wc_descriptions = ['Cutting', 'Molding', 'Assembly Line A', 'Painting Booth', 'Packaging', 'Welding Station', 'CNC Machining']

    production_supervisors = df_employees[df_employees['Department'] == 'Production']['Employee_ID'].tolist()
    if not production_supervisors:
        production_supervisors = df_employees['Employee_ID'].tolist() # Fallback if no specific 'Production' dept

    for _, plant_row in df_plants.iterrows():
        plant_id = plant_row['Plant_ID']
        for i in range(num_work_centers_per_plant):
            wc_id = f"{plant_id}_WC{str(i+1).zfill(3)}"
            work_centers.append({
                'Work_Center_ID': wc_id,
                'Plant_ID': plant_id,
                'Work_Center_Description': random.choice(wc_descriptions) + f" {random.randint(1,5)}",
                'Usage': random.choice(usage_types),
                'Capacity_Category': random.choice(capacity_categories),
                'Production_Supervisor_ID': random.choice(production_supervisors)
            })
    return pd.DataFrame(work_centers)

# --- 6. Dim_Equipment Generation ---
def generate_dim_equipment(df_work_centers, num_equipment_per_work_center):
    equipment_list = []
    manufacturers = ['Siemens', 'ABB', 'Fanuc', 'KUKA', 'Bosch', 'GE']
    equipment_types = {
        'CNC Machine': ['Lathe', 'Mill', 'Drill'],
        'Assembly Line': ['Robot', 'Conveyor', 'Workstation'],
        'Injection Molder': ['Horizontal', 'Vertical'],
        'Painting Booth': ['Automated', 'Manual'],
        'Welding Station': ['MIG', 'TIG', 'Arc']
    }
    
    for _, wc_row in df_work_centers.iterrows():
        wc_id = wc_row['Work_Center_ID']
        plant_id = wc_row['Plant_ID']
        wc_desc = wc_row['Work_Center_Description'] # Use WC description to suggest equipment type

        for i in range(num_equipment_per_work_center):
            eq_id = f"{wc_id}_EQP{str(i+1).zfill(2)}"
            manufacturer = random.choice(manufacturers)
            serial_number = fake.bothify(text='SN-##########')
            construction_year = random.randint(START_DATE.year - 10, START_DATE.year - 1) # Built up to 10 years ago

            eq_type_desc_base = 'Generic Equipment'
            if 'CNC' in wc_desc: eq_type_desc_base = 'CNC Machine'
            elif 'Assembly' in wc_desc: eq_type_desc_base = 'Assembly Line'
            elif 'Molding' in wc_desc: eq_type_desc_base = 'Injection Molder'
            elif 'Painting' in wc_desc: eq_type_desc_base = 'Painting Booth'
            elif 'Welding' in wc_desc: eq_type_desc_base = 'Welding Station'
            
            eq_type_desc = random.choice(equipment_types.get(eq_type_desc_base, [eq_type_desc_base]))
            eq_type_code = "".join([word[0] for word in eq_type_desc.split()]).upper()[:10] # e.g., 'CNCMACHI'

            equipment_list.append({
                'Equipment_ID': eq_id,
                'Plant_ID': plant_id,
                'Manufacturer': manufacturer,
                'Serial_Number': serial_number,
                'Construction_Year': construction_year,
                'Equipment_Type_Desc': eq_type_desc,
                'Equipment_Type_Code': eq_type_code
            })
    return pd.DataFrame(equipment_list)

# --- 7. Dim_Vendor Generation ---
def generate_dim_vendor(num_vendors):
    vendors = []
    vendor_names = ["Global Supplies Inc.", "EnergyCo Solutions", "RawMat Distributors", "Logistics Pros", "Quality Components Ltd."]
    for i in range(num_vendors):
        vendor_id = f"VNDR{str(i+1).zfill(3)}"
        vendors.append({
            'Vendor_ID': vendor_id,
            'Vendor_Name': fake.company() + " " + random.choice(vendor_names),
            'Vendor_City': fake.city(),
            'Vendor_Country': fake.country()
        })
    return pd.DataFrame(vendors)

# --- Main Generation Logic for Master Data ---
print("--- Generating Master Data ---")
df_dim_date = generate_dim_date(START_DATE, END_DATE)
save_dataframe_to_csv(df_dim_date, 'dim_date.csv')

df_dim_plant = generate_dim_plant(NUM_PLANTS)
save_dataframe_to_csv(df_dim_plant, 'dim_plant.csv')

df_dim_material = generate_dim_material(NUM_MATERIALS)
save_dataframe_to_csv(df_dim_material, 'dim_material.csv')

df_dim_employee = generate_dim_employee(NUM_EMPLOYEES)
save_dataframe_to_csv(df_dim_employee, 'dim_employee.csv')

df_dim_work_center = generate_dim_work_center(df_dim_plant, NUM_WORK_CENTERS_PER_PLANT, df_dim_employee)
save_dataframe_to_csv(df_dim_work_center, 'dim_work_center.csv')

df_dim_equipment = generate_dim_equipment(df_dim_work_center, NUM_EQUIPMENT_PER_WORK_CENTER)
save_dataframe_to_csv(df_dim_equipment, 'dim_equipment.csv')

df_dim_vendor = generate_dim_vendor(NUM_VENDORS)
save_dataframe_to_csv(df_dim_vendor, 'dim_vendor.csv')

print("\nMaster Data Generation Complete. Proceeding to Fact Data (in next part).")