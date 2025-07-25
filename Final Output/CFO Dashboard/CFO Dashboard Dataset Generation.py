import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# --- Configuration Parameters ---
START_DATE = datetime(2023, 4, 1)
END_DATE = datetime(2024, 3, 31)
OUTPUT_DIR = "Dataset"

# Enterprise Size Volumes (Adjust these for different company sizes)
BASE_GL_POSTINGS_PER_DAY = 200 # Average daily GL postings
BASE_ASSET_ACQUISITIONS_PER_MONTH = 50 # New assets
BASE_CUSTOMER_INVOICES_PER_DAY = 100 # New customer invoices
BASE_VENDOR_INVOICES_PER_DAY = 50 # New vendor invoices
BASE_MATERIAL_MOVEMENTS_PER_DAY = 150 # Material movements

# Financial Ratio Targets (used for guiding data generation)
TARGET_EBITDA_MARGIN = 0.20 # 20%
TARGET_NET_PROFIT_MARGIN = 0.07 # 7%
TARGET_ROE = 0.15 # 15%
TARGET_WORKING_CAPITAL_RATIO = 1.75
TARGET_DEBT_TO_EQUITY_RATIO = 0.8
TARGET_DSO_DAYS = 35 # Days Sales Outstanding
TARGET_DIO_DAYS = 60 # Days Inventory Outstanding
TARGET_DPO_DAYS = 50 # Days Payable Outstanding
TARGET_INVENTORY_TURNOVER = 6 # times per year
TARGET_QUICK_RATIO = 1.0

# GL Account Ranges (as defined in business logic)
GL_ACCOUNTS = {
    "ASSET": {"range": (100000, 199999), "type": "Balance Sheet", "groups": {
        "Cash": (100000, 109999), "Receivables": (110000, 119999), "Inventory": (120000, 129999),
        "Fixed Assets Gross": (130000, 139999), "Accumulated Depreciation": (140000, 149999),
        "Other Current Assets": (150000, 159999), "Other Non-Current Assets": (160000, 199999)
    }},
    "LIABILITY": {"range": (200000, 299999), "type": "Balance Sheet", "groups": {
        "Payables": (200000, 209999), "Short-Term Debt": (210000, 219999), "Accrued Expenses": (220000, 229999),
        "Long-Term Debt": (230000, 239999), "Other Liabilities": (240000, 299999)
    }},
    "EQUITY": {"range": (300000, 399999), "type": "Balance Sheet", "groups": {
        "Share Capital": (300000, 309999), "Retained Earnings": (310000, 319999)
    }},
    "REVENUE": {"range": (400000, 499999), "type": "P&L", "groups": {
        "Sales Revenue": (400000, 409999), "Other Revenue": (410000, 499999)
    }},
    "EXPENSE": {"range": (500000, 699999), "type": "P&L", "groups": {
        "COGS": (500000, 509999), "Operating Expenses": (510000, 599999),
        "Depreciation Expense": (600000, 609999), "Interest Expense": (610000, 619999),
        "Tax Expense": (620000, 629999), "Other Expenses": (630000, 699999)
    }}
}

# --- Helper Functions ---
def save_dataframe_to_csv(df, filename):
    """Saves a pandas DataFrame to a CSV file in the specified output directory."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    filepath = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(filepath, index=False)
    print(f"Saved {len(df)} records to {filepath}")

def get_fiscal_period(date, fiscal_year_start_month=4):
    """Determines fiscal year and period based on a given date and fiscal year start month."""
    year = date.year
    month = date.month
    if month >= fiscal_year_start_month:
        fiscal_year = year
        fiscal_month = month - fiscal_year_start_month + 1
    else:
        fiscal_year = year - 1
        fiscal_month = month + (12 - fiscal_year_start_month) + 1
    fiscal_quarter = (fiscal_month - 1) // 3 + 1
    return fiscal_year, fiscal_month, fiscal_quarter

def get_gl_account_details(gl_account_num):
    """Returns the account group and type for a given GL account number."""
    for group, details in GL_ACCOUNTS.items():
        start, end = details["range"]
        if start <= gl_account_num <= end:
            for sub_group, sub_range in details["groups"].items():
                if sub_range[0] <= gl_account_num <= sub_range[1]:
                    return sub_group, details["type"]
    return "Unknown", "Unknown"

# --- Data Generation Functions ---

def generate_dim_date(start_date, end_date, fiscal_year_start_month=4):
    """Generates the dim_date table."""
    dates = []
    current_date = start_date
    while current_date <= end_date:
        fiscal_year, fiscal_month, fiscal_quarter = get_fiscal_period(current_date, fiscal_year_start_month)
        
        dates.append({
            "date_key": current_date.strftime("%Y-%m-%d"),
            "year": current_date.year,
            "quarter": (current_date.month - 1) // 3 + 1,
            "month": current_date.month,
            "month_name": current_date.strftime("%B"),
            "week": current_date.isocalendar()[1],
            "day_of_week": current_date.weekday() + 1, # Monday is 1, Sunday is 7
            "day_name": current_date.strftime("%A"),
            "fiscal_year": fiscal_year,
            "fiscal_quarter": fiscal_quarter,
            "fiscal_month": fiscal_month,
            "is_weekend": current_date.weekday() >= 5, # Saturday (5) or Sunday (6)
            "is_holiday": False, # For simplicity, no holidays generated
            "month_start_date": current_date.replace(day=1).strftime("%Y-%m-%d"),
            "quarter_start_date": (current_date.replace(month=((current_date.month - 1) // 3) * 3 + 1, day=1)).strftime("%Y-%m-%d"),
            "year_start_date": current_date.replace(month=1, day=1).strftime("%Y-%m-%d")
        })
        current_date += timedelta(days=1)
    return pd.DataFrame(dates)

def generate_skat_gl_accounts():
    """Generates the skat_gl_accounts table."""
    accounts = []
    for group_name, details in GL_ACCOUNTS.items():
        for sub_group, (start, end) in details["groups"].items():
            for i in range(start, min(end + 1, start + 20)): # Generate up to 20 accounts per sub-group
                gl_account = str(i).zfill(6)
                accounts.append({
                    "gl_account": gl_account,
                    "account_description": f"{sub_group} Account {gl_account}",
                    "account_group": group_name,
                    "account_type": details["type"]
                })
    return pd.DataFrame(accounts)

def generate_t001_company_codes():
    """Generates the t001_company_codes table."""
    return pd.DataFrame([
        {"company_code": "US01", "company_name": "Global Corp US", "country": "USA", "currency": "USD", "chart_of_accounts": "INT"},
        {"company_code": "DE01", "company_name": "Global Corp DE", "country": "GER", "currency": "EUR", "chart_of_accounts": "INT"},
        {"company_code": "IN01", "company_name": "Global Corp IN", "country": "IND", "currency": "INR", "chart_of_accounts": "INT"},
    ])

def generate_cepc_profit_centers(num_profit_centers=20):
    """Generates the cepc_profit_centers table."""
    profit_centers = []
    for i in range(num_profit_centers):
        pc_id = f"PC{str(i+1).zfill(3)}"
        profit_centers.append({
            "profit_center": pc_id,
            "controlling_area": "A000", # Common controlling area
            "profit_center_name": f"Profit Center {pc_id}",
            "valid_from": (START_DATE - timedelta(days=365)).strftime("%Y-%m-%d"),
            "valid_to": (END_DATE + timedelta(days=365)).strftime("%Y-%m-%d")
        })
    return pd.DataFrame(profit_centers)

def generate_csks_cost_centers(num_cost_centers=30):
    """Generates the csks_cost_centers table."""
    cost_centers = []
    for i in range(num_cost_centers):
        cc_id = f"CC{str(i+1).zfill(3)}"
        cost_centers.append({
            "cost_center": cc_id,
            "controlling_area": "A000", # Common controlling area
            "cost_center_name": f"Cost Center {cc_id}",
            "valid_from": (START_DATE - timedelta(days=365)).strftime("%Y-%m-%d"),
            "valid_to": (END_DATE + timedelta(days=365)).strftime("%Y-%m-%d")
        })
    return pd.DataFrame(cost_centers)

def generate_anla_asset_master(num_assets=2000):
    """Generates the anla_asset_master table."""
    assets = []
    company_codes = ["US01", "DE01", "IN01"]
    asset_classes = ["MACH", "VEH", "BLDG", "COMP"] # Machinery, Vehicle, Building, Computer
    
    for i in range(num_assets):
        company_code = random.choice(company_codes)
        asset_class = random.choice(asset_classes)
        
        # Capitalization date before or within the period
        cap_date = START_DATE - timedelta(days=random.randint(0, 730)) # Up to 2 years before start
        if cap_date < datetime(2022, 1, 1): # Ensure not too old for demo
            cap_date = datetime(2022, 1, 1)
        
        deact_date = None
        if random.random() < 0.05: # 5% chance of deactivation within period
            deact_date = random.choice(pd.date_range(START_DATE, END_DATE))
        
        assets.append({
            "asset_number": f"A{str(i+1).zfill(7)}",
            "sub_number": "0", # For simplicity, no sub-numbers
            "company_code": company_code,
            "asset_class": asset_class,
            "asset_description": f"{asset_class} Asset {i+1}",
            "capitalization_date": cap_date.strftime("%Y-%m-%d"),
            "deactivation_date": deact_date.strftime("%Y-%m-%d") if deact_date else None
        })
    return pd.DataFrame(assets)

def generate_mbew_material_valuation(num_materials=3000):
    """Generates the mbew_material_valuation table."""
    materials = []
    plants = ["PL01", "PL02", "PL03"] # Example plants
    
    for i in range(num_materials):
        plant = random.choice(plants)
        material_num = f"MAT{str(i+1).zfill(7)}"
        
        # Simulate realistic stock and values
        total_stock = round(max(0, np.random.normal(500, 200)), 0) # Avg 500 units
        standard_price = round(max(10, np.random.lognormal(2.5, 0.8)), 2) # Skewed towards lower prices
        moving_average_price = round(standard_price * random.uniform(0.95, 1.05), 2)
        total_value_stock = round(total_stock * moving_average_price, 2)
        
        materials.append({
            "material_number": material_num,
            "plant": plant,
            "valuation_type": "", # For simplicity, no split valuation
            "valuation_area": plant, # Valuation area same as plant
            "standard_price": standard_price,
            "moving_average_price": moving_average_price,
            "total_stock": total_stock,
            "total_value_stock": total_value_stock,
            "last_update_date": (END_DATE - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        })
    return pd.DataFrame(materials)


def generate_faglflexa_and_bseg(dim_date_df, skat_gl_accounts_df, t001_company_codes_df, cepc_profit_centers_df, csks_cost_centers_df, anla_asset_master_df):
    """
    Generates faglflexa_gl_items and bseg_doc_segment tables.
    Focus on creating transactions that broadly support the target ratios.
    """
    faglflexa_records = []
    bseg_records = []
    
    # Pre-select master data IDs for efficiency
    gl_accounts_df = skat_gl_accounts_df.copy()
    company_codes = t001_company_codes_df["company_code"].tolist()
    profit_centers = cepc_profit_centers_df["profit_center"].tolist()
    cost_centers = csks_cost_centers_df["cost_center"].tolist()

    # Filter GL accounts by type for easier selection
    cash_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Cash')]['gl_account'].tolist()
    receivable_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Receivables')]['gl_account'].tolist()
    inventory_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Inventory')]['gl_account'].tolist()
    fixed_asset_gross_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Fixed Assets Gross')]['gl_account'].tolist()
    acc_dep_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Accumulated Depreciation')]['gl_account'].tolist()
    payable_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Payables')]['gl_account'].tolist()
    short_term_debt_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Short-Term Debt')]['gl_account'].tolist()
    long_term_debt_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Long-Term Debt')]['gl_account'].tolist()
    equity_accounts = gl_accounts_df[gl_accounts_df['account_group'] == 'EQUITY']['gl_account'].tolist()
    revenue_accounts = gl_accounts_df[gl_accounts_df['account_group'] == 'REVENUE']['gl_account'].tolist()
    cogs_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('COGS')]['gl_account'].tolist()
    operating_expense_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Operating Expenses')]['gl_account'].tolist()
    depreciation_expense_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Depreciation Expense')]['gl_account'].tolist()
    interest_expense_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Interest Expense')]['gl_account'].tolist()
    tax_expense_accounts = gl_accounts_df[gl_accounts_df['account_description'].str.contains('Tax Expense')]['gl_account'].tolist()
    
    faglflexa_id_counter = 1
    bseg_id_counter = 1

    # Initial Balance Sheet Entries (before START_DATE)
    # Simulate opening balances for key balance sheet accounts
    initial_balance_date = START_DATE - timedelta(days=1)
    doc_num_prefix = "IB"
    
    # Assets (Debits)
    for i, acc in enumerate(random.sample(cash_accounts, 1) + random.sample(receivable_accounts, 1) + random.sample(inventory_accounts, 1) + random.sample(fixed_asset_gross_accounts, 1)):
        amount = round(np.random.normal(500000, 100000), 2)
        if acc in acc_dep_accounts: amount = -amount # Accumulated depreciation has credit balance
        
        doc_num = f"{doc_num_prefix}{str(bseg_id_counter).zfill(8)}"
        bseg_records.append({
            "document_number": doc_num,
            "company_code": "US01",
            "fiscal_year": initial_balance_date.year,
            "line_item": i + 1,
            "gl_account": acc,
            "amount_in_doc_curr": amount,
            "currency": t001_company_codes_df[t001_company_codes_df['company_code'] == "US01"]['currency'].iloc[0],
            "debit_credit_indicator": "S" if amount >= 0 else "H",
            "cost_center": random.choice(cost_centers),
            "profit_center": random.choice(profit_centers),
            "special_gl_indicator": None,
            "text": "Initial Balance"
        })
        faglflexa_records.append({
            "id": faglflexa_id_counter,
            "company_code": "US01",
            "gl_account": acc,
            "posting_date": initial_balance_date.strftime("%Y-%m-%d"),
            "document_number": doc_num,
            "item_number": i + 1,
            "amount_local": amount,
            "amount_group": amount,
            "currency_local": t001_company_codes_df[t001_company_codes_df['company_code'] == "US01"]['currency'].iloc[0],
            "currency_group": "USD",
            "debit_credit_indicator": "S" if amount >= 0 else "H",
            "cost_center": random.choice(cost_centers),
            "profit_center": random.choice(profit_centers),
            "fiscal_year": initial_balance_date.year,
            "fiscal_period": get_fiscal_period(initial_balance_date)[1],
            "value_date": initial_balance_date.strftime("%Y-%m-%d"),
            "reference_document": None
        })
        faglflexa_id_counter += 1
        bseg_id_counter += 1

    # Liabilities & Equity (Credits)
    for i, acc in enumerate(random.sample(payable_accounts, 1) + random.sample(short_term_debt_accounts, 1) + random.sample(long_term_debt_accounts, 1) + random.sample(equity_accounts, 1)):
        amount = round(np.random.normal(300000, 50000), 2)
        doc_num = f"{doc_num_prefix}{str(bseg_id_counter).zfill(8)}"
        bseg_records.append({
            "document_number": doc_num,
            "company_code": "US01",
            "fiscal_year": initial_balance_date.year,
            "line_item": i + 1,
            "gl_account": acc,
            "amount_in_doc_curr": -amount, # Credit balance
            "currency": t001_company_codes_df[t001_company_codes_df['company_code'] == "US01"]['currency'].iloc[0],
            "debit_credit_indicator": "H",
            "cost_center": random.choice(cost_centers),
            "profit_center": random.choice(profit_centers),
            "special_gl_indicator": None,
            "text": "Initial Balance"
        })
        faglflexa_records.append({
            "id": faglflexa_id_counter,
            "company_code": "US01",
            "gl_account": acc,
            "posting_date": initial_balance_date.strftime("%Y-%m-%d"),
            "document_number": doc_num,
            "item_number": i + 1,
            "amount_local": -amount,
            "amount_group": -amount,
            "currency_local": t001_company_codes_df[t001_company_codes_df['company_code'] == "US01"]['currency'].iloc[0],
            "currency_group": "USD",
            "debit_credit_indicator": "H",
            "cost_center": random.choice(cost_centers),
            "profit_center": random.choice(profit_centers),
            "fiscal_year": initial_balance_date.year,
            "fiscal_period": get_fiscal_period(initial_balance_date)[1],
            "value_date": initial_balance_date.strftime("%Y-%m-%d"),
            "reference_document": None
        })
        faglflexa_id_counter += 1
        bseg_id_counter += 1

    # Main Transactional Data Generation
    for index, row in dim_date_df.iterrows():
        current_date = datetime.strptime(row["date_key"], "%Y-%m-%d")
        if row["is_weekend"]:
            continue # Skip weekends for most business transactions

        num_postings = int(BASE_GL_POSTINGS_PER_DAY * (1 + 0.2 * np.sin(current_date.month * np.pi / 6))) # Seasonality
        if current_date.day > 25: # End of month push
            num_postings = int(num_postings * 1.2)

        for _ in range(num_postings):
            company_code = random.choice(company_codes)
            profit_center = random.choice(profit_centers)
            cost_center = random.choice(cost_centers)
            
            # Simulate a simple double-entry booking
            doc_num = f"DOC{str(bseg_id_counter).zfill(8)}"
            
            # Scenario: Revenue Recognition (Debit Cash/Receivables, Credit Revenue)
            if random.random() < 0.4: # 40% chance of revenue posting
                revenue_amount = round(np.random.normal(5000, 1000), 2)
                debit_account = random.choice(cash_accounts + receivable_accounts)
                credit_account = random.choice(revenue_accounts)

                # Debit Entry
                bseg_records.append({
                    "document_number": doc_num, "company_code": company_code, "fiscal_year": row["fiscal_year"],
                    "line_item": 1, "gl_account": debit_account, "amount_in_doc_curr": revenue_amount,
                    "currency": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "debit_credit_indicator": "S", "cost_center": cost_center, "profit_center": profit_center,
                    "special_gl_indicator": None, "text": "Sales Revenue"
                })
                faglflexa_records.append({
                    "id": faglflexa_id_counter, "company_code": company_code, "gl_account": debit_account,
                    "posting_date": row["date_key"], "document_number": doc_num, "item_number": 1,
                    "amount_local": revenue_amount, "amount_group": revenue_amount,
                    "currency_local": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "currency_group": "USD", "debit_credit_indicator": "S", "cost_center": cost_center,
                    "profit_center": profit_center, "fiscal_year": row["fiscal_year"], "fiscal_period": row["fiscal_month"],
                    "value_date": row["date_key"], "reference_document": None
                })
                faglflexa_id_counter += 1

                # Credit Entry
                bseg_records.append({
                    "document_number": doc_num, "company_code": company_code, "fiscal_year": row["fiscal_year"],
                    "line_item": 2, "gl_account": credit_account, "amount_in_doc_curr": -revenue_amount,
                    "currency": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "debit_credit_indicator": "H", "cost_center": cost_center, "profit_center": profit_center,
                    "special_gl_indicator": None, "text": "Sales Revenue"
                })
                faglflexa_records.append({
                    "id": faglflexa_id_counter, "company_code": company_code, "gl_account": credit_account,
                    "posting_date": row["date_key"], "document_number": doc_num, "item_number": 2,
                    "amount_local": -revenue_amount, "amount_group": -revenue_amount,
                    "currency_local": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "currency_group": "USD", "debit_credit_indicator": "H", "cost_center": cost_center,
                    "profit_center": profit_center, "fiscal_year": row["fiscal_year"], "fiscal_period": row["fiscal_month"],
                    "value_date": row["date_key"], "reference_document": None
                })
                faglflexa_id_counter += 1
                bseg_id_counter += 1

            # Scenario: Expense Posting (Debit Expense, Credit Cash/Payables)
            elif random.random() < 0.7: # 30% chance of expense posting
                expense_amount = round(np.random.normal(1000, 300), 2)
                debit_account = random.choice(operating_expense_accounts)
                credit_account = random.choice(cash_accounts + payable_accounts)
                
                # Debit Entry
                bseg_records.append({
                    "document_number": doc_num, "company_code": company_code, "fiscal_year": row["fiscal_year"],
                    "line_item": 1, "gl_account": debit_account, "amount_in_doc_curr": expense_amount,
                    "currency": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "debit_credit_indicator": "S", "cost_center": cost_center, "profit_center": profit_center,
                    "special_gl_indicator": None, "text": "Operating Expense"
                })
                faglflexa_records.append({
                    "id": faglflexa_id_counter, "company_code": company_code, "gl_account": debit_account,
                    "posting_date": row["date_key"], "document_number": doc_num, "item_number": 1,
                    "amount_local": expense_amount, "amount_group": expense_amount,
                    "currency_local": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "currency_group": "USD", "debit_credit_indicator": "S", "cost_center": cost_center,
                    "profit_center": profit_center, "fiscal_year": row["fiscal_year"], "fiscal_period": row["fiscal_month"],
                    "value_date": row["date_key"], "reference_document": None
                })
                faglflexa_id_counter += 1

                # Credit Entry
                bseg_records.append({
                    "document_number": doc_num, "company_code": company_code, "fiscal_year": row["fiscal_year"],
                    "line_item": 2, "gl_account": credit_account, "amount_in_doc_curr": -expense_amount,
                    "currency": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "debit_credit_indicator": "H", "cost_center": cost_center, "profit_center": profit_center,
                    "special_gl_indicator": None, "text": "Operating Expense"
                })
                faglflexa_records.append({
                    "id": faglflexa_id_counter, "company_code": company_code, "gl_account": credit_account,
                    "posting_date": row["date_key"], "document_number": doc_num, "item_number": 2,
                    "amount_local": -expense_amount, "amount_group": -expense_amount,
                    "currency_local": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "currency_group": "USD", "debit_credit_indicator": "H", "cost_center": cost_center,
                    "profit_center": profit_center, "fiscal_year": row["fiscal_year"], "fiscal_period": row["fiscal_month"],
                    "value_date": row["date_key"], "reference_document": None
                })
                faglflexa_id_counter += 1
                bseg_id_counter += 1

    # Add monthly depreciation postings
    for company_code in company_codes:
        for month_offset in range(0, (END_DATE.year - START_DATE.year) * 12 + END_DATE.month - START_DATE.month + 1):
            dep_date = (START_DATE + timedelta(days=30 * month_offset)).replace(day=28) # End of month
            
            # Get assets active in this period
            active_assets = anla_asset_master_df[
                (anla_asset_master_df['company_code'] == company_code) &
                (pd.to_datetime(anla_asset_master_df['capitalization_date']) <= dep_date) &
                ((pd.to_datetime(anla_asset_master_df['deactivation_date']).isna()) | 
                 (pd.to_datetime(anla_asset_master_df['deactivation_date']) >= dep_date))
            ]
            
            if not active_assets.empty:
                total_asset_value = active_assets['asset_number'].count() * 50000 # Avg asset value for depreciation calc
                monthly_depreciation_amount = round(total_asset_value * 0.10 / 12, 2) # 10% annual depreciation
                
                doc_num = f"DEP{str(bseg_id_counter).zfill(8)}"
                
                # Debit Depreciation Expense
                bseg_records.append({
                    "document_number": doc_num, "company_code": company_code, "fiscal_year": dep_date.year,
                    "line_item": 1, "gl_account": random.choice(depreciation_expense_accounts), "amount_in_doc_curr": monthly_depreciation_amount,
                    "currency": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "debit_credit_indicator": "S", "cost_center": random.choice(cost_centers), "profit_center": random.choice(profit_centers),
                    "special_gl_indicator": None, "text": "Monthly Depreciation"
                })
                faglflexa_records.append({
                    "id": faglflexa_id_counter, "company_code": company_code, "gl_account": random.choice(depreciation_expense_accounts),
                    "posting_date": dep_date.strftime("%Y-%m-%d"), "document_number": doc_num, "item_number": 1,
                    "amount_local": monthly_depreciation_amount, "amount_group": monthly_depreciation_amount,
                    "currency_local": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "currency_group": "USD", "debit_credit_indicator": "S", "cost_center": random.choice(cost_centers),
                    "profit_center": random.choice(profit_centers), "fiscal_year": dep_date.year, "fiscal_period": get_fiscal_period(dep_date)[1],
                    "value_date": dep_date.strftime("%Y-%m-%d"), "reference_document": None
                })
                faglflexa_id_counter += 1

                # Credit Accumulated Depreciation
                bseg_records.append({
                    "document_number": doc_num, "company_code": company_code, "fiscal_year": dep_date.year,
                    "line_item": 2, "gl_account": random.choice(acc_dep_accounts), "amount_in_doc_curr": -monthly_depreciation_amount,
                    "currency": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "debit_credit_indicator": "H", "cost_center": random.choice(cost_centers), "profit_center": random.choice(profit_centers),
                    "special_gl_indicator": None, "text": "Monthly Depreciation"
                })
                faglflexa_records.append({
                    "id": faglflexa_id_counter, "company_code": company_code, "gl_account": random.choice(acc_dep_accounts),
                    "posting_date": dep_date.strftime("%Y-%m-%d"), "document_number": doc_num, "item_number": 2,
                    "amount_local": -monthly_depreciation_amount, "amount_group": -monthly_depreciation_amount,
                    "currency_local": t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0],
                    "currency_group": "USD", "debit_credit_indicator": "H", "cost_center": random.choice(cost_centers),
                    "profit_center": random.choice(profit_centers), "fiscal_year": dep_date.year, "fiscal_period": get_fiscal_period(dep_date)[1],
                    "value_date": dep_date.strftime("%Y-%m-%d"), "reference_document": None
                })
                faglflexa_id_counter += 1
                bseg_id_counter += 1

    faglflexa_df = pd.DataFrame(faglflexa_records)
    bseg_df = pd.DataFrame(bseg_records)
    return faglflexa_df, bseg_df

def generate_anlc_asset_values(anla_asset_master_df, dim_date_df):
    """Generates the anlc_asset_values table based on asset master data."""
    anlc_records = []
    
    # Ensure capitalization_date is datetime object
    anla_asset_master_df['capitalization_date'] = pd.to_datetime(anla_asset_master_df['capitalization_date'])
    anla_asset_master_df['deactivation_date'] = pd.to_datetime(anla_asset_master_df['deactivation_date'])

    for index, asset in anla_asset_master_df.iterrows():
        # Only consider assets capitalized before or within the period
        if asset['capitalization_date'] > END_DATE:
            continue
        
        # Determine the start fiscal year for this asset's values
        start_fiscal_year, _, _ = get_fiscal_period(asset['capitalization_date'])
        
        # Iterate through fiscal years relevant to the demo period
        for year_offset in range(0, (END_DATE.year - START_DATE.year) + 2): # Cover 2 fiscal years + 1 for buffer
            current_fiscal_year = START_DATE.year + year_offset
            
            # Check if asset was active for at least part of this fiscal year
            fiscal_year_start = datetime(current_fiscal_year, 4, 1) # Assuming April 1st fiscal year start
            fiscal_year_end = datetime(current_fiscal_year + 1, 3, 31)

            if asset['capitalization_date'] > fiscal_year_end:
                continue # Asset not yet capitalized in this fiscal year
            if asset['deactivation_date'] is not None and asset['deactivation_date'] < fiscal_year_start:
                continue # Asset already deactivated before this fiscal year

            # Simulate acquisition value
            acquisition_value = round(np.random.normal(50000, 15000), 2)
            
            # Simulate accumulated depreciation (simplified linear depreciation)
            # Calculate full years active until the *end* of the current fiscal year or deactivation
            active_until = min(fiscal_year_end, asset['deactivation_date'] if asset['deactivation_date'] is not None else END_DATE + timedelta(days=365*10))
            
            years_active_end_fy = (active_until - asset['capitalization_date']).days / 365.25
            
            # Ensure accumulated depreciation doesn't exceed acquisition value
            acc_dep_at_year_end = round(min(acquisition_value * 0.10 * max(0, years_active_end_fy), acquisition_value * 0.9), 2) # 10% annual dep, max 90%

            # Net Book Value
            net_book_value = round(acquisition_value - acc_dep_at_year_end, 2)
            if net_book_value < 0: net_book_value = 0 # Cannot be negative

            anlc_records.append({
                "company_code": asset["company_code"],
                "asset_number": asset["asset_number"],
                "sub_number": asset["sub_number"],
                "fiscal_year": current_fiscal_year,
                "acquisition_value": acquisition_value,
                "accumulated_depreciation": acc_dep_at_year_end,
                "net_book_value": net_book_value,
                "currency": "USD" # Assuming USD for asset values for simplicity or based on company code if needed
            })
    return pd.DataFrame(anlc_records)

def generate_dfkkop_customer_line_items(dim_date_df, t001_company_codes_df):
    """Generates dfkkop_customer_line_items table."""
    dfkkop_records = []
    customer_id_counter = 1
    doc_num_counter = 1
    
    company_codes = t001_company_codes_df["company_code"].tolist()

    for index, row in dim_date_df.iterrows():
        current_date = datetime.strptime(row["date_key"], "%Y-%m-%d")
        if row["is_weekend"]:
            continue

        num_invoices = int(BASE_CUSTOMER_INVOICES_PER_DAY * (1 + 0.1 * np.sin(current_date.month * np.pi / 6)))
        for _ in range(num_invoices):
            company_code = random.choice(company_codes)
            customer_id = f"CUST{str(random.randint(1, 1000)).zfill(4)}" # 1000 unique customers
            document_number = f"INV{str(doc_num_counter).zfill(8)}"
            
            amount = round(np.random.normal(1500, 500), 2)
            currency = t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0]
            
            # Invoice (Debit)
            dfkkop_records.append({
                "customer_id": customer_id,
                "company_code": company_code,
                "document_number": document_number,
                "line_item": 1,
                "posting_date": row["date_key"],
                "document_date": row["date_key"],
                "clearing_date": None, # Will be filled by payments
                "amount_in_doc_currency": amount,
                "currency": currency,
                "debit_credit_indicator": "S", # Debit
                "clearing_document": None,
                "open_item_status": "Open",
                "due_date": (current_date + timedelta(days=TARGET_DSO_DAYS + random.randint(-5, 10))).strftime("%Y-%m-%d")
            })
            doc_num_counter += 1

            # Simulate payments for some invoices (clearing them)
            if random.random() < 0.7: # 70% of invoices get paid
                payment_date = current_date + timedelta(days=random.randint(5, TARGET_DSO_DAYS + 10))
                if payment_date <= END_DATE:
                    clearing_doc_num = f"CLR{str(doc_num_counter).zfill(8)}"
                    dfkkop_records.append({
                        "customer_id": customer_id,
                        "company_code": company_code,
                        "document_number": clearing_doc_num,
                        "line_item": 1,
                        "posting_date": payment_date.strftime("%Y-%m-%d"),
                        "document_date": payment_date.strftime("%Y-%m-%d"),
                        "clearing_date": payment_date.strftime("%Y-%m-%d"),
                        "amount_in_doc_currency": -amount, # Credit for payment
                        "currency": currency,
                        "debit_credit_indicator": "H", # Credit
                        "clearing_document": document_number, # Links to the invoice
                        "open_item_status": "Cleared",
                        "due_date": None
                    })
                    # Update the original invoice to 'Cleared'
                    for rec in dfkkop_records:
                        if rec["document_number"] == document_number and rec["company_code"] == company_code:
                            rec["clearing_date"] = payment_date.strftime("%Y-%m-%d")
                            rec["clearing_document"] = clearing_doc_num
                            rec["open_item_status"] = "Cleared"
                            break
                    doc_num_counter += 1
    
    return pd.DataFrame(dfkkop_records)

def generate_dfkko_vendor_line_items(dim_date_df, t001_company_codes_df):
    """Generates dfkko_vendor_line_items table."""
    dfkko_records = []
    vendor_id_counter = 1
    doc_num_counter = 1

    company_codes = t001_company_codes_df["company_code"].tolist()

    for index, row in dim_date_df.iterrows():
        current_date = datetime.strptime(row["date_key"], "%Y-%m-%d")
        if row["is_weekend"]:
            continue

        num_invoices = int(BASE_VENDOR_INVOICES_PER_DAY * (1 + 0.1 * np.sin(current_date.month * np.pi / 6)))
        for _ in range(num_invoices):
            company_code = random.choice(company_codes)
            vendor_id = f"VEND{str(random.randint(1, 500)).zfill(3)}" # 500 unique vendors
            document_number = f"POINV{str(doc_num_counter).zfill(8)}"
            
            amount = round(np.random.normal(800, 300), 2)
            currency = t001_company_codes_df[t001_company_codes_df['company_code'] == company_code]['currency'].iloc[0]

            # Invoice (Credit)
            dfkko_records.append({
                "vendor_id": vendor_id,
                "company_code": company_code,
                "document_number": document_number,
                "line_item": 1,
                "posting_date": row["date_key"],
                "document_date": row["date_key"],
                "clearing_date": None, # Will be filled by payments
                "amount_in_doc_currency": -amount, # Credit for vendor invoice
                "currency": currency,
                "debit_credit_indicator": "H", # Credit
                "clearing_document": None,
                "open_item_status": "Open",
                "due_date": (current_date + timedelta(days=TARGET_DPO_DAYS + random.randint(-5, 10))).strftime("%Y-%m-%d")
            })
            doc_num_counter += 1

            # Simulate payments for some invoices
            if random.random() < 0.8: # 80% of vendor invoices get paid
                payment_date = current_date + timedelta(days=random.randint(5, TARGET_DPO_DAYS + 10))
                if payment_date <= END_DATE:
                    clearing_doc_num = f"VPAY{str(doc_num_counter).zfill(8)}"
                    dfkko_records.append({
                        "vendor_id": vendor_id,
                        "company_code": company_code,
                        "document_number": clearing_doc_num,
                        "line_item": 1,
                        "posting_date": payment_date.strftime("%Y-%m-%d"),
                        "document_date": payment_date.strftime("%Y-%m-%d"),
                        "clearing_date": payment_date.strftime("%Y-%m-%d"),
                        "amount_in_doc_currency": amount, # Debit for payment
                        "currency": currency,
                        "debit_credit_indicator": "S", # Debit
                        "clearing_document": document_number, # Links to the invoice
                        "open_item_status": "Cleared",
                        "due_date": None
                    })
                    # Update the original invoice to 'Cleared'
                    for rec in dfkko_records:
                        if rec["document_number"] == document_number and rec["company_code"] == company_code:
                            rec["clearing_date"] = payment_date.strftime("%Y-%m-%d")
                            rec["clearing_document"] = clearing_doc_num
                            rec["open_item_status"] = "Cleared"
                            break
                    doc_num_counter += 1
    return pd.DataFrame(dfkko_records)


def generate_cfo_dataset():
    """Generates all CFO dashboard demo datasets."""
    
    print("Starting CFO Demo Data Generation...")
    
    # 1. Dimension Tables
    dim_date_df = generate_dim_date(START_DATE, END_DATE)
    save_dataframe_to_csv(dim_date_df, "dim_date.csv")

    skat_gl_accounts_df = generate_skat_gl_accounts()
    save_dataframe_to_csv(skat_gl_accounts_df, "skat_gl_accounts.csv")

    t001_company_codes_df = generate_t001_company_codes()
    save_dataframe_to_csv(t001_company_codes_df, "t001_company_codes.csv")

    cepc_profit_centers_df = generate_cepc_profit_centers()
    save_dataframe_to_csv(cepc_profit_centers_df, "cepc_profit_centers.csv")

    csks_cost_centers_df = generate_csks_cost_centers()
    save_dataframe_to_csv(csks_cost_centers_df, "csks_cost_centers.csv")

    anla_asset_master_df = generate_anla_asset_master()
    save_dataframe_to_csv(anla_asset_master_df, "anla_asset_master.csv")

    mbew_material_valuation_df = generate_mbew_material_valuation()
    save_dataframe_to_csv(mbew_material_valuation_df, "mbew_material_valuation.csv")

    # 2. Fact Tables (Interdependent generation)
    # GL Items and Document Segments
    faglflexa_gl_items_df, bseg_doc_segment_df = generate_faglflexa_and_bseg(
        dim_date_df, skat_gl_accounts_df, t001_company_codes_df, cepc_profit_centers_df, csks_cost_centers_df, anla_asset_master_df
    )
    save_dataframe_to_csv(faglflexa_gl_items_df, "faglflexa_gl_items.csv")
    save_dataframe_to_csv(bseg_doc_segment_df, "bseg_doc_segment.csv")

    # Asset Values
    anlc_asset_values_df = generate_anlc_asset_values(anla_asset_master_df, dim_date_df)
    save_dataframe_to_csv(anlc_asset_values_df, "anlc_asset_values.csv")

    # Customer Line Items
    dfkkop_customer_line_items_df = generate_dfkkop_customer_line_items(dim_date_df, t001_company_codes_df)
    save_dataframe_to_csv(dfkkop_customer_line_items_df, "dfkkop_customer_line_items.csv")

    # Vendor Line Items
    dfkko_vendor_line_items_df = generate_dfkko_vendor_line_items(dim_date_df, t001_company_codes_df)
    save_dataframe_to_csv(dfkko_vendor_line_items_df, "dfkko_vendor_line_items.csv")

    print("\nCFO Demo Data Generation Completed!")

if __name__ == "__main__":
    generate_cfo_dataset()