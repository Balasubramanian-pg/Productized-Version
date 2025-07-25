import pandas as pd
import numpy as np
from faker import Faker
import datetime
from datetime import timedelta
import os
import random

# --- Configuration ---
START_DATE = datetime.date(2023, 4, 1) # April 1, 2023
END_DATE = datetime.date(2025, 3, 31)   # March 31, 2025 (2 years of data)
OUTPUT_DIR = "cfo_demo_data"
NUM_COMPANIES = 3 # Enterprise size: 3-5 companies
NUM_GL_ACCOUNTS = 700 # Enterprise size: 500-1000 accounts
NUM_PROFIT_CENTERS = 70 # Enterprise size: 50-100
NUM_COST_CENTERS = 150 # Enterprise size: 100-200
NUM_ASSETS = 3000 # Enterprise size: 2k-5k assets
NUM_MATERIALS = 1000 # Enterprise size: 500-1500 materials
NUM_CUSTOMERS = 7000 # Enterprise size: 5k-10k customers
NUM_VENDORS = 1500 # Enterprise size: 1k-2k vendors
# Average daily transaction volumes for Enterprise scale (adjusted to hit targets)
AVG_DAILY_GL_POSTINGS = 200 # Roughly 5k-10k per month per company
AVG_DAILY_INVENTORY_MOVEMENTS = 80
AVG_DAILY_AR_ITEMS = 30
AVG_DAILY_AP_ITEMS = 20
# KPI Target Ranges (approximate, generation aims for these)
TARGET_REVENUE_GROWTH_YOY = (0.08, 0.12) # 8-12%
TARGET_EBITDA_MARGIN = (0.18, 0.25)    # 18-25%
TARGET_ROE = (0.12, 0.18)              # 12-18%
TARGET_WORKING_CAPITAL_RATIO = (1.3, 1.8)
TARGET_DEBT_TO_EQUITY_RATIO = (0.6, 1.2)
TARGET_CCC = (50, 70) # Days
TARGET_DSO = (45, 55) # Days
TARGET_DIO = (60, 70) # Days
TARGET_DPO = (55, 65) # Days
TARGET_DSCR = (1.5, 2.5) # >1.5
TARGET_ROA = (0.06, 0.10)              # 6-10%
TARGET_INVENTORY_TURNOVER = (4.0, 6.0) # Times per year
TARGET_QUICK_RATIO = (0.9, 1.2)
# --- Faker Initialization ---
fake = Faker('en_US') # Use US locale for realistic names/addresses
# --- Helper Functions ---
def generate_dates(start_date, end_date):
    """Generates the dim_date table with April-March fiscal calendar."""
    dates = []
    current_date = start_date
    while current_date <= end_date:
        fiscal_year = current_date.year if current_date.month >= 4 else current_date.year - 1
        fiscal_quarter = ((current_date.month - 4) // 3) + 1
        if fiscal_quarter <= 0: # Adjust for Jan-Mar being Q4 of previous fiscal year
             fiscal_quarter += 4
        fiscal_month = (current_date.month - 4) % 12 + 1
        is_weekend = current_date.weekday() >= 5 # Saturday or Sunday

        dates.append({
            'date_key': current_date,
            'year': current_date.year,
            'quarter': (current_date.month - 1) // 3 + 1,
            'month': current_date.month,
            'month_name': current_date.strftime('%B'),
            'week': current_date.isocalendar()[1],
            'day_of_week': current_date.weekday() + 1,
            'day_name': current_date.strftime('%A'),
            'fiscal_year': fiscal_year,
            'fiscal_quarter': fiscal_quarter,
            'fiscal_month': fiscal_month,
            'is_weekend': is_weekend,
            'is_holiday': False, # Can be expanded with a holiday calendar
            'month_start_date': current_date.replace(day=1),
            'quarter_start_date': datetime.date(current_date.year, (current_date.month - 1) // 3 * 3 + 1, 1),
            'year_start_date': datetime.date(current_date.year, 1, 1),
        })
        current_date += timedelta(days=1)
    df = pd.DataFrame(dates)
    return df

def generate_master_data(num_companies, num_gl_accounts, num_profit_centers, num_cost_centers, num_assets, num_materials, num_customers, num_vendors):
    """Generates all dimension tables."""
    print("Generating Master Data...")
    # dim_company_codes
    companies = []
    for i in range(num_companies):
        company_code = f"CO{i+1:02d}"
        companies.append({
            'company_code': company_code,
            'company_name': fake.company() + (f" Global {i+1}" if i > 0 else " Corp"),
            'country': fake.country_code(),
            'currency': 'USD' if i == 0 else random.choice(['EUR', 'GBP', 'CAD', 'JPY']),
            'chart_of_accounts': 'INT'
        })
    df_companies = pd.DataFrame(companies)
    # dim_gl_accounts
    gl_accounts = []
    # Explicitly add Cash/Bank accounts to ensure they exist
    gl_accounts.append({'gl_account': "100000", 'account_description': 'Cash - Operating Account', 'account_group': 'Assets', 'account_type': 'Balance Sheet'})
    gl_accounts.append({'gl_account': "100001", 'account_description': 'Bank - Main Account', 'account_group': 'Assets', 'account_type': 'Balance Sheet'})
    gl_accounts.append({'gl_account': "100002", 'account_description': 'Accounts Receivable', 'account_group': 'Assets', 'account_type': 'Balance Sheet'})
    gl_accounts.append({'gl_account': "200000", 'account_description': 'Accounts Payable', 'account_group': 'Liabilities', 'account_type': 'Balance Sheet'})
    gl_accounts.append({'gl_account': "600001", 'account_description': 'Depreciation Expense', 'account_group': 'Expenses', 'account_type': 'P&L'})
    # Asset Accounts (1xxxx)
    for i in range(1, 100): gl_accounts.append({'gl_account': f"100{i+2:03d}", 'account_description': fake.bs(), 'account_group': 'Assets', 'account_type': 'Balance Sheet'})
    # Liability Accounts (2xxxx)
    for i in range(1, 100): gl_accounts.append({'gl_account': f"200{i+1:03d}", 'account_description': fake.bs(), 'account_group': 'Liabilities', 'account_type': 'Balance Sheet'})
    # Equity Accounts (3xxxx)
    for i in range(50): gl_accounts.append({'gl_account': f"300{i+1:03d}", 'account_description': fake.bs(), 'account_group': 'Equity', 'account_type': 'Balance Sheet'})
    # Revenue Accounts (4xxxx)
    for i in range(150): gl_accounts.append({'gl_account': f"400{i+1:03d}", 'account_description': fake.word().capitalize() + ' Revenue', 'account_group': 'Revenue', 'account_type': 'P&L'})
    # COGS Accounts (5xxxx)
    for i in range(50): gl_accounts.append({'gl_account': f"500{i+1:03d}", 'account_description': fake.word().capitalize() + ' COGS', 'account_group': 'COGS', 'account_type': 'P&L'})
    # Expense Accounts (6xxxx)
    for i in range(1, 250): gl_accounts.append({'gl_account': f"600{i+1:03d}", 'account_description': fake.word().capitalize() + ' Expense', 'account_group': 'Expenses', 'account_type': 'P&L'})
    # Non-Operating / Interest / Tax (7xxxx)
    gl_accounts.append({'gl_account': "700001", 'account_description': 'Interest Income', 'account_group': 'Other Income', 'account_type': 'P&L'})
    gl_accounts.append({'gl_account': "700002", 'account_description': 'Interest Expense', 'account_group': 'Other Expenses', 'account_type': 'P&L'})
    gl_accounts.append({'gl_account': "700003", 'account_description': 'Income Tax Expense', 'account_group': 'Taxes', 'account_type': 'P&L'})
    df_gl_accounts = pd.DataFrame(gl_accounts)

    # dim_profit_centers
    profit_centers = []
    for i in range(num_profit_centers):
        profit_centers.append({
            'profit_center': f"PC{i+1:03d}",
            'controlling_area': 'CA01', # Assuming one controlling area
            'profit_center_name': fake.city() + ' Operations',
            'valid_from': fake.date_between(start_date=START_DATE - timedelta(days=365*5), end_date=START_DATE),
            'valid_to': END_DATE + timedelta(days=365*5)
        })
    df_profit_centers = pd.DataFrame(profit_centers)
    # dim_cost_centers
    cost_centers = []
    for i in range(num_cost_centers):
        cost_centers.append({
            'cost_center': f"CC{i+1:04d}",
            'controlling_area': 'CA01',
            'cost_center_name': fake.word().capitalize() + ' Dept ' + str(i+1),
            'valid_from': fake.date_between(start_date=START_DATE - timedelta(days=365*5), end_date=START_DATE),
            'valid_to': END_DATE + timedelta(days=365*5)
        })
    df_cost_centers = pd.DataFrame(cost_centers)
    # dim_assets
    assets = []
    asset_classes = ['BUILDING', 'MACHINERY', 'VEHICLE', 'COMPUTER', 'FURNITURE']
    for i in range(num_assets):
        comp_code = random.choice(df_companies['company_code'].tolist())
        assets.append({
            'asset_number': f"A{i+1:05d}",
            'sub_number': '0', # Simple sub-number
            'company_code': comp_code,
            'asset_class': random.choice(asset_classes),
            'asset_description': fake.sentence(nb_words=4),
            'capitalization_date': fake.date_between(start_date=START_DATE - timedelta(days=365*2), end_date=END_DATE - timedelta(days=30)),
            'deactivation_date': None # Most are active
        })
    df_assets = pd.DataFrame(assets)
    # dim_materials
    materials = []
    for i in range(num_materials):
        materials.append({
            'material_number': f"M{i+1:05d}",
            'plant': 'PL01', # Assuming one main plant for simplicity
            'valuation_type': 'STD',
            'valuation_area': 'PL01',
            'standard_price': round(random.uniform(10.0, 5000.0), 2),
            'moving_average_price': round(random.uniform(9.0, 5100.0), 2),
        })
    df_materials = pd.DataFrame(materials)
    # dim_customers
    customers = []
    for i in range(num_customers):
        customers.append({
            'customer_number': f"CUST{i+1:05d}",
            'customer_name': fake.company(),
            'country': fake.country_code(),
            'city': fake.city()
        })
    df_customers = pd.DataFrame(customers)
    # dim_vendors
    vendors = []
    for i in range(num_vendors):
        vendors.append({
            'vendor_number': f"VEND{i+1:05d}",
            'vendor_name': fake.company() + ' Suppliers',
            'country': fake.country_code(),
            'city': fake.city()
        })
    df_vendors = pd.DataFrame(vendors)
    return df_companies, df_gl_accounts, df_profit_centers, df_cost_centers, \
           df_assets, df_materials, df_customers, df_vendors

def generate_fact_data(df_dates, df_companies, df_gl_accounts, df_profit_centers, df_cost_centers,
                       df_assets, df_materials, df_customers, df_vendors):
    """Generates all fact tables based on business logic."""
    print("Generating Fact Data...")
    # --- Pre-calculate daily base volumes with seasonality ---
    total_days = (END_DATE - START_DATE).days + 1
    daily_revenue_factors = []
    daily_expense_factors = []
    daily_ar_factors = []
    daily_ap_factors = []
    daily_inv_factors = []
    for _, row in df_dates.iterrows():
        # Overall growth factor over time
        growth_factor = 1 + (TARGET_REVENUE_GROWTH_YOY[0] + (TARGET_REVENUE_GROWTH_YOY[1] - TARGET_REVENUE_GROWTH_YOY[0]) * random.random()) * ((row['date_key'] - START_DATE).days / 365.0)
        # Seasonality (Q4 spike for Oct-Dec, adjusted for Apr-Mar fiscal)
        # Assuming Q4 of fiscal year (Jan-Mar) is peak for this fiscal calendar
        month_of_fiscal_year = row['fiscal_month']
        season_factor = 1.0
        if 10 <= row['month'] <= 12: # Calendar Q4 - often a general business peak
            season_factor = 1.25 # Higher volume
        elif row['month'] >= 1 and row['month'] <= 3: # Fiscal Q4 (Jan-Mar)
             season_factor = 1.35 # Higher volume for fiscal year end close
        # Weekend factor
        weekend_factor = 0.2 if row['is_weekend'] else 1.0 # Much lower on weekends
        daily_revenue_factors.append(growth_factor * season_factor * weekend_factor)
        daily_expense_factors.append(growth_factor * weekend_factor * random.uniform(0.9, 1.1)) # Expenses less seasonal
        daily_ar_factors.append(growth_factor * season_factor * weekend_factor * random.uniform(0.9, 1.1))
        daily_ap_factors.append(growth_factor * weekend_factor * random.uniform(0.8, 1.2))
        daily_inv_factors.append(growth_factor * weekend_factor * random.uniform(0.9, 1.1))
    # --- fact_gl_postings ---
    gl_postings = []
    gl_account_types = df_gl_accounts.set_index('gl_account')['account_type'].to_dict()
    gl_account_groups = df_gl_accounts.set_index('gl_account')['account_group'].to_dict()
    # Pre-determine total revenue for KPI calculation
    # Base annual revenue per company, then adjust by daily factors
    base_annual_revenue_per_company = 250_000_000 # For an Enterprise

    company_annual_revenues = {comp: base_annual_revenue_per_company * random.uniform(0.9, 1.1) for comp in df_companies['company_code']}
    for day_idx, (idx, date_row) in enumerate(df_dates.iterrows()):
        current_date = date_row['date_key']

        for company_code in df_companies['company_code']:
            daily_rev_budget = company_annual_revenues[company_code] * (daily_revenue_factors[day_idx] / sum(daily_revenue_factors)) # Distribute annual revenue based on daily factors
            num_daily_gl = int(AVG_DAILY_GL_POSTINGS * daily_revenue_factors[day_idx] / (sum(daily_revenue_factors)/total_days)) # Scale daily postings

            # Simulate high-level P&L and Balance Sheet to hit KPIs
            # Revenue (4xxxx accounts)
            rev_accounts = df_gl_accounts[df_gl_accounts['account_group'] == 'Revenue']['gl_account'].tolist()
            if rev_accounts and daily_rev_budget > 0:
                gl_postings.append({
                    'gl_posting_id': len(gl_postings) + 1,
                    'company_code': company_code,
                    'gl_account': random.choice(rev_accounts),
                    'posting_date': current_date,
                    'document_number': f"DOC{len(gl_postings)+1:08d}",
                    'item_number': 1,
                    'amount_local': round(daily_rev_budget * random.uniform(0.9, 1.1), 2),
                    'amount_group': round(daily_rev_budget * random.uniform(0.9, 1.1) * random.uniform(0.95, 1.05), 2),
                    'currency_local': 'USD', # Simplified for demo
                    'currency_group': 'USD',
                    'debit_credit_indicator': 'H', # Credit for Revenue
                    'cost_center': None,
                    'profit_center': random.choice(df_profit_centers['profit_center']),
                    'fiscal_year': date_row['fiscal_year'],
                    'fiscal_period': date_row['fiscal_month'],
                    'value_date': current_date,
                    'reference_document': fake.uuid4()[:8].upper(),
                    'special_gl_indicator': None,
                    'transaction_text': fake.sentence(nb_words=3)
                })
            # COGS (5xxxx accounts) - typically 50-70% of revenue
            cogs_accounts = df_gl_accounts[df_gl_accounts['account_group'] == 'COGS']['gl_account'].tolist()
            if cogs_accounts and daily_rev_budget > 0:
                 gl_postings.append({
                    'gl_posting_id': len(gl_postings) + 1,
                    'company_code': company_code,
                    'gl_account': random.choice(cogs_accounts),
                    'posting_date': current_date,
                    'document_number': f"DOC{len(gl_postings)+1:08d}",
                    'item_number': 1,
                    'amount_local': round(daily_rev_budget * random.uniform(0.5, 0.7), 2), # COGS percentage
                    'amount_group': round(daily_rev_budget * random.uniform(0.5, 0.7) * random.uniform(0.95, 1.05), 2),
                    'currency_local': 'USD',
                    'currency_group': 'USD',
                    'debit_credit_indicator': 'S', # Debit for COGS
                    'cost_center': None,
                    'profit_center': random.choice(df_profit_centers['profit_center']),
                    'fiscal_year': date_row['fiscal_year'],
                    'fiscal_period': date_row['fiscal_month'],
                    'value_date': current_date,
                    'reference_document': fake.uuid4()[:8].upper(),
                    'special_gl_indicator': None,
                    'transaction_text': fake.sentence(nb_words=3)
                })
            # Operating Expenses (6xxxx accounts) - to hit EBITDA target
            # Target EBITDA = Revenue * Target EBITDA Margin
            # Operating Exp = Revenue - COGS - Target EBITDA
            target_ebitda_amount = daily_rev_budget * random.uniform(*TARGET_EBITDA_MARGIN)
            approx_operating_expense = daily_rev_budget * random.uniform(0.2, 0.3) # General range

            exp_accounts = df_gl_accounts[df_gl_accounts['account_group'] == 'Expenses']['gl_account'].tolist()
            if exp_accounts and approx_operating_expense > 0:
                for _ in range(int(num_daily_gl / 5)): # Simulate multiple expense postings
                    gl_postings.append({
                        'gl_posting_id': len(gl_postings) + 1,
                        'company_code': company_code,
                        'gl_account': random.choice(exp_accounts),
                        'posting_date': current_date,
                        'document_number': f"DOC{len(gl_postings)+1:08d}",
                        'item_number': 1,
                        'amount_local': round(approx_operating_expense * random.uniform(0.01, 0.05), 2), # Small individual expenses
                        'amount_group': round(approx_operating_expense * random.uniform(0.01, 0.05) * random.uniform(0.95, 1.05), 2),
                        'currency_local': 'USD',
                        'currency_group': 'USD',
                        'debit_credit_indicator': 'S', # Debit for Expenses
                        'cost_center': random.choice(df_cost_centers['cost_center']),
                        'profit_center': random.choice(df_profit_centers['profit_center']),
                        'fiscal_year': date_row['fiscal_year'],
                        'fiscal_period': date_row['fiscal_month'],
                        'value_date': current_date,
                        'reference_document': fake.uuid4()[:8].upper(),
                        'special_gl_indicator': None,
                        'transaction_text': fake.sentence(nb_words=3)
                    })

            # Asset Movements / Depreciation (monthly for anlc)
            if current_date.day == 15: # Mid-month for monthly depreciation postings
                for asset_idx, asset_row in df_assets[df_assets['company_code'] == company_code].iterrows():
                    if asset_row['capitalization_date'] <= current_date:
                        # Extract last 3 digits, convert to int, handle non-numeric gracefully
                        try:
                            asset_num_last3 = int(''.join(filter(str.isdigit, asset_row['asset_number'][-3:])))
                        except Exception:
                            asset_num_last3 = 0
                        depreciation_amount = round(asset_num_last3 * 0.5 + random.uniform(50, 500), 2) # Simulate depreciation
                        # Check if 'Depreciation Expense' GL account exists before adding
                        if '600001' in df_gl_accounts['gl_account'].tolist():
                             gl_postings.append({
                                'gl_posting_id': len(gl_postings) + 1,
                                'company_code': company_code,
                                'gl_account': '600001', # Example Depreciation Expense GL
                                'posting_date': current_date,
                                'document_number': f"DOC{len(gl_postings)+1:08d}",
                                'item_number': 1,
                                'amount_local': depreciation_amount,
                                'amount_group': depreciation_amount,
                                'currency_local': 'USD',
                                'currency_group': 'USD',
                                'debit_credit_indicator': 'S',
                                'cost_center': random.choice(df_cost_centers['cost_center']),
                                'profit_center': random.choice(df_profit_centers['profit_center']),
                                'fiscal_year': date_row['fiscal_year'],
                                'fiscal_period': date_row['fiscal_month'],
                                'value_date': current_date,
                                'reference_document': f"DEP{asset_row['asset_number']}-{date_row['fiscal_year']}{date_row['fiscal_month']}",
                                'special_gl_indicator': None,
                                'transaction_text': f"Depreciation for Asset {asset_row['asset_number']}"
                            })

            # Simulate cash/bank movements for P&L reconciliation (simplified)
            # This helps balance the GL for cash flow later
            if random.random() < 0.2: # Some days have cash entries
                # Use the explicitly added Cash/Bank accounts
                cash_bank_accounts = df_gl_accounts[df_gl_accounts['account_description'].str.contains('Cash|Bank', case=False)]['gl_account'].tolist()
                if cash_bank_accounts: # Ensure list is not empty before sampling
                    cash_account = random.choice(cash_bank_accounts)
                    amount = round(daily_rev_budget * random.uniform(0.01, 0.05), 2)
                    gl_postings.append({
                        'gl_posting_id': len(gl_postings) + 1,
                        'company_code': company_code,
                        'gl_account': cash_account,
                        'posting_date': current_date,
                        'document_number': f"DOC{len(gl_postings)+1:08d}",
                        'item_number': 1,
                        'amount_local': amount,
                        'amount_group': amount,
                        'currency_local': 'USD',
                        'currency_group': 'USD',
                        'debit_credit_indicator': random.choice(['S', 'H']), # Random debit/credit
                        'cost_center': None,
                        'profit_center': None,
                        'fiscal_year': date_row['fiscal_year'],
                        'fiscal_period': date_row['fiscal_month'],
                        'value_date': current_date,
                        'reference_document': fake.uuid4()[:8].upper(),
                        'special_gl_indicator': None,
                        'transaction_text': fake.sentence(nb_words=3)
                    })
    df_gl_postings = pd.DataFrame(gl_postings)
    # --- fact_asset_movements ---
    asset_movements = []
    asset_id_counter = 0
    for _, date_row in df_dates.iterrows():
        current_date = date_row['date_key']
        if current_date.day == 15: # Monthly depreciation posting
            for _, asset_row in df_assets.iterrows():
                if asset_row['capitalization_date'] <= current_date:
                    depreciation_amount = round(random.uniform(100.0, 5000.0), 2)
                    asset_movements.append({
                        'asset_movement_id': len(asset_movements) + 1,
                        'asset_number': asset_row['asset_number'],
                        'sub_number': asset_row['sub_number'],
                        'company_code': asset_row['company_code'],
                        'fiscal_year': date_row['fiscal_year'],
                        'depreciation_area': '01',
                        'posting_date': current_date,
                        'acquisition_value': 0.0, # Not an acquisition record
                        'ordinary_depreciation_posted': depreciation_amount,
                        'net_book_value': None, # Calculated in BI
                        'movement_type': 'Depreciation'
                    })

            # Simulate new asset acquisitions (fewer)
            if random.random() < 0.1: # 10% chance per month to acquire some assets
                num_new_assets = random.randint(1, 5)
                for _ in range(num_new_assets):
                    asset_id_counter += 1
                    new_asset_num = f"A{NUM_ASSETS + asset_id_counter:05d}"
                    comp_code = random.choice(df_companies['company_code'].tolist())
                    acquisition_value = round(random.uniform(5000.0, 100000.0), 2)
                    asset_movements.append({
                        'asset_movement_id': len(asset_movements) + 1,
                        'asset_number': new_asset_num,
                        'sub_number': '0',
                        'company_code': comp_code,
                        'fiscal_year': date_row['fiscal_year'],
                        'depreciation_area': '01',
                        'posting_date': current_date,
                        'acquisition_value': acquisition_value,
                        'ordinary_depreciation_posted': 0.0,
                        'net_book_value': None,
                        'movement_type': 'Acquisition'
                    })
                    # Add to dim_assets temporarily to ensure referential integrity for subsequent movements
                    df_assets.loc[len(df_assets)] = {
                        'asset_number': new_asset_num,
                        'sub_number': '0',
                        'company_code': comp_code,
                        'asset_class': random.choice(['MACHINERY', 'COMPUTER']),
                        'asset_description': fake.sentence(nb_words=4),
                        'capitalization_date': current_date,
                        'deactivation_date': None
                    }
    df_asset_movements = pd.DataFrame(asset_movements)
    # --- fact_inventory_movements ---
    inventory_movements = []
    material_prices = df_materials.set_index('material_number')['standard_price'].to_dict()
    for day_idx, (idx, date_row) in enumerate(df_dates.iterrows()):
        current_date = date_row['date_key']
        num_daily_inv = int(AVG_DAILY_INVENTORY_MOVEMENTS * daily_inv_factors[day_idx] / (sum(daily_inv_factors)/total_days))
        for _ in range(num_daily_inv):
            material = random.choice(df_materials['material_number'].tolist())
            comp_code = random.choice(df_companies['company_code'].tolist())
            movement_type = random.choices(['GR', 'GI_SALES', 'GI_PROD', 'TRSF'], weights=[0.4, 0.3, 0.2, 0.1], k=1)[0]
            quantity = round(random.uniform(1, 100), 2)

            unit = 'EA'
            amount = round(quantity * material_prices.get(material, 100), 2)
            inventory_movements.append({
                'inventory_movement_id': len(inventory_movements) + 1,
                'material_document': f"MDOC{len(inventory_movements)+1:08d}",
                'material_document_year': current_date.year,
                'material_document_item': 1,
                'material_number': material,
                'plant': 'PL01',
                'storage_location': 'SL01',
                'movement_type': movement_type,
                'posting_date': current_date,
                'quantity': quantity,
                'unit_of_measure': unit,
                'amount_local': amount
            })
    df_inventory_movements = pd.DataFrame(inventory_movements)
    # --- fact_ar_open_items ---
    ar_items = []
    for day_idx, (idx, date_row) in enumerate(df_dates.iterrows()):
        current_date = date_row['date_key']
        num_daily_ar = int(AVG_DAILY_AR_ITEMS * daily_ar_factors[day_idx] / (sum(daily_ar_factors)/total_days))
        for _ in range(num_daily_ar):
            customer = random.choice(df_customers['customer_number'].tolist())
            comp_code = random.choice(df_companies['company_code'].tolist())
            amount = round(random.uniform(500.0, 50000.0), 2)
            due_date = current_date + timedelta(days=int(random.gauss(TARGET_DSO[0], 5))) # Aim for DSO

            # Simulate clearing: 85% paid on time/early, 10% slightly late, 5% very late
            rand_clear = random.random()
            if rand_clear < 0.85: # Paid on time/early
                clearing_date = current_date + timedelta(days=random.randint(5, 30))
            elif rand_clear < 0.95: # Slightly late
                clearing_date = due_date + timedelta(days=random.randint(1, 15))
            else: # Very late / open
                clearing_date = None if current_date < END_DATE - timedelta(days=60) else current_date + timedelta(days=random.randint(15, 60)) # Ensure some stay open
            # Ensure clearing_date is not in future
            if clearing_date and clearing_date > END_DATE:
                clearing_date = None
            ar_items.append({
                'ar_item_id': len(ar_items) + 1,
                'document_number': f"AR{len(ar_items)+1:08d}",
                'company_code': comp_code,
                'fiscal_year': date_row['fiscal_year'],
                'line_item': 1,
                'customer_number': customer,
                'posting_date': current_date,
                'clearing_date': clearing_date,
                'due_date': due_date,
                'amount_local': amount,
                'currency': 'USD',
                'debit_credit_indicator': 'S',
                'is_open': clearing_date is None
            })
    df_ar_open_items = pd.DataFrame(ar_items)
    # --- fact_ap_open_items ---
    ap_items = []
    for day_idx, (idx, date_row) in enumerate(df_dates.iterrows()):
        current_date = date_row['date_key']
        num_daily_ap = int(AVG_DAILY_AP_ITEMS * daily_ap_factors[day_idx] / (sum(daily_ap_factors)/total_days))
        for _ in range(num_daily_ap):
            vendor = random.choice(df_vendors['vendor_number'].tolist())
            comp_code = random.choice(df_companies['company_code'].tolist())
            amount = round(random.uniform(100.0, 20000.0), 2)
            due_date = current_date + timedelta(days=int(random.gauss(TARGET_DPO[0], 5))) # Aim for DPO
            # Simulate clearing: 80% paid on time/early, 15% slightly late, 5% very late
            rand_clear = random.random()
            if rand_clear < 0.80: # Paid on time/early
                clearing_date = current_date + timedelta(days=random.randint(5, 30))
            elif rand_clear < 0.95: # Slightly late
                clearing_date = due_date + timedelta(days=random.randint(1, 10))
            else: # Very late / open
                clearing_date = None if current_date < END_DATE - timedelta(days=45) else current_date + timedelta(days=random.randint(10, 45))
            if clearing_date and clearing_date > END_DATE:
                clearing_date = None

            ap_items.append({
                'ap_item_id': len(ap_items) + 1,
                'document_number': f"AP{len(ap_items)+1:08d}",
                'company_code': comp_code,
                'fiscal_year': date_row['fiscal_year'],
                'line_item': 1,
                'vendor_number': vendor,
                'posting_date': current_date,
                'clearing_date': clearing_date,
                'due_date': due_date,
                'amount_local': amount,
                'currency': 'USD',
                'debit_credit_indicator': 'H', # Credit for AP
                'is_open': clearing_date is None
            })
    df_ap_open_items = pd.DataFrame(ap_items)
    return df_gl_postings, df_asset_movements, df_inventory_movements, df_ar_open_items, df_ap_open_items

# --- Main Execution ---
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating data for period: {START_DATE} to {END_DATE} (Fiscal Year: April-March)")
    print(f"Output directory: {OUTPUT_DIR}")
    # 1. Generate Date Dimension
    df_dates = generate_dates(START_DATE, END_DATE)
    df_dates.to_csv(os.path.join(OUTPUT_DIR, 'dim_date.csv'), index=False)
    print(f"Generated dim_date: {len(df_dates)} rows")
    # 2. Generate Master Data Dimensions
    df_companies, df_gl_accounts, df_profit_centers, df_cost_centers, \
    df_assets, df_materials, df_customers, df_vendors = generate_master_data(
        NUM_COMPANIES, NUM_GL_ACCOUNTS, NUM_PROFIT_CENTERS, NUM_COST_CENTERS,
        NUM_ASSETS, NUM_MATERIALS, NUM_CUSTOMERS, NUM_VENDORS
    )
    df_companies.to_csv(os.path.join(OUTPUT_DIR, 'dim_company_codes.csv'), index=False)
    print(f"Generated dim_company_codes: {len(df_companies)} rows")
    df_gl_accounts.to_csv(os.path.join(OUTPUT_DIR, 'dim_gl_accounts.csv'), index=False)
    print(f"Generated dim_gl_accounts: {len(df_gl_accounts)} rows")
    df_profit_centers.to_csv(os.path.join(OUTPUT_DIR, 'dim_profit_centers.csv'), index=False)
    print(f"Generated dim_profit_centers: {len(df_profit_centers)} rows")
    df_cost_centers.to_csv(os.path.join(OUTPUT_DIR, 'dim_cost_centers.csv'), index=False)
    print(f"Generated dim_cost_centers: {len(df_cost_centers)} rows")
    df_assets.to_csv(os.path.join(OUTPUT_DIR, 'dim_assets.csv'), index=False)
    print(f"Generated dim_assets: {len(df_assets)} rows")
    df_materials.to_csv(os.path.join(OUTPUT_DIR, 'dim_materials.csv'), index=False)
    print(f"Generated dim_materials: {len(df_materials)} rows")
    df_customers.to_csv(os.path.join(OUTPUT_DIR, 'dim_customers.csv'), index=False)
    print(f"Generated dim_customers: {len(df_customers)} rows")
    df_vendors.to_csv(os.path.join(OUTPUT_DIR, 'dim_vendors.csv'), index=False)
    print(f"Generated dim_vendors: {len(df_vendors)} rows")
    # 3. Generate Fact Tables
    df_gl_postings, df_asset_movements, df_inventory_movements, \
    df_ar_open_items, df_ap_open_items = generate_fact_data(
        df_dates, df_companies, df_gl_accounts, df_profit_centers, df_cost_centers,
        df_assets, df_materials, df_customers, df_vendors
    )
    df_gl_postings.to_csv(os.path.join(OUTPUT_DIR, 'fact_gl_postings.csv'), index=False)
    print(f"Generated fact_gl_postings: {len(df_gl_postings)} rows")
    df_asset_movements.to_csv(os.path.join(OUTPUT_DIR, 'fact_asset_movements.csv'), index=False)
    print(f"Generated fact_asset_movements: {len(df_asset_movements)} rows")
    df_inventory_movements.to_csv(os.path.join(OUTPUT_DIR, 'fact_inventory_movements.csv'), index=False)
    print(f"Generated fact_inventory_movements: {len(df_inventory_movements)} rows")
    df_ar_open_items.to_csv(os.path.join(OUTPUT_DIR, 'fact_ar_open_items.csv'), index=False)
    print(f"Generated fact_ar_open_items: {len(df_ar_open_items)} rows")
    df_ap_open_items.to_csv(os.path.join(OUTPUT_DIR, 'fact_ap_open_items.csv'), index=False)
    print(f"Generated fact_ap_open_items: {len(df_ap_open_items)} rows")
    print("\nData generation complete! Check the 'cfo_demo_data' directory.")
