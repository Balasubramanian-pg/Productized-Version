import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from faker import Faker
import uuid

fake = Faker()
np.random.seed(42)
random.seed(42)

# Date range setup
start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)
date_range = pd.date_range(start=start_date, end=end_date, freq='D')

# Filter out weekends for business days
business_days = [d for d in date_range if d.weekday() < 5]

print(f"Generating data for {len(business_days)} business days from {start_date.date()} to {end_date.date()}")

# ===== DATE DIMENSION =====
def create_date_dimension():
    dates = []
    for date in date_range:
        fiscal_year = date.year if date.month >= 4 else date.year - 1  # April start fiscal year
        fiscal_month = ((date.month - 4) % 12) + 1
        fiscal_quarter = ((fiscal_month - 1) // 3) + 1
        
        dates.append({
            'date_key': date.date(),
            'year': date.year,
            'quarter': ((date.month - 1) // 3) + 1,
            'month': date.month,
            'month_name': date.strftime('%B'),
            'week': date.isocalendar()[1],
            'day_of_week': date.weekday() + 1,
            'day_name': date.strftime('%A'),
            'fiscal_year': fiscal_year,
            'fiscal_quarter': fiscal_quarter,
            'fiscal_month': fiscal_month,
            'is_weekend': date.weekday() >= 5,
            'is_holiday': False  # Simplified - could add holiday logic
        })
    return pd.DataFrame(dates)

# ===== MASTER DATA =====
def create_customers(n=50):
    customers = []
    for i in range(n):
        customers.append({
            'customer_id': f'C{str(i+1000).zfill(6)}',
            'customer_name': fake.company(),
            'customer_group': random.choice(['RETAIL', 'WHOLESALE', 'ENTERPRISE']),
            'country': random.choice(['US', 'CA', 'DE', 'GB', 'FR']),
            'region': random.choice(['NORTH', 'SOUTH', 'EAST', 'WEST', 'CENTRAL']),
            'city': fake.city(),
            'created_date': fake.date_between(start_date='-5y', end_date=start_date),
            'customer_type': random.choice(['NEW', 'EXISTING'])
        })
    return pd.DataFrame(customers)

def create_materials(n=200):
    materials = []
    product_lines = ['ELECTRONICS', 'AUTOMOTIVE', 'INDUSTRIAL', 'CONSUMER', 'HEALTHCARE']
    for i in range(n):
        product_line = random.choice(product_lines)
        materials.append({
            'material_id': f'MAT{str(i+10000).zfill(6)}',
            'material_description': f'{product_line} Product {i+1}',
            'material_group': f'{product_line[:3]}{random.randint(100, 999)}',
            'product_line': product_line,
            'standard_cost': round(random.uniform(10, 1000), 2),
            'currency': 'USD'
        })
    return pd.DataFrame(materials)

def create_gl_accounts():
    accounts = [
        # Revenue accounts
        ('4000000', 'Product Sales Revenue', 'REVENUE', 'Revenue'),
        ('4010000', 'Service Revenue', 'REVENUE', 'Revenue'),
        ('4020000', 'Other Revenue', 'REVENUE', 'Revenue'),
        # COGS accounts
        ('5000000', 'Cost of Goods Sold', 'COGS', 'Expense'),
        ('5010000', 'Material Costs', 'COGS', 'Expense'),
        ('5020000', 'Labor Costs', 'COGS', 'Expense'),
        # Operating expenses
        ('6000000', 'Sales & Marketing', 'OPEX', 'Expense'),
        ('6010000', 'Research & Development', 'OPEX', 'Expense'),
        ('6020000', 'General & Administrative', 'OPEX', 'Expense'),
        ('6030000', 'Employee Costs', 'OPEX', 'Expense'),
        # Assets
        ('1000000', 'Cash and Cash Equivalents', 'ASSET', 'Asset'),
        ('1100000', 'Accounts Receivable', 'ASSET', 'Asset'),
        ('1200000', 'Inventory', 'ASSET', 'Asset'),
        # Liabilities
        ('2000000', 'Accounts Payable', 'LIABILITY', 'Liability'),
        ('2100000', 'Accrued Expenses', 'LIABILITY', 'Liability')
    ]
    
    gl_df = []
    for acc in accounts:
        gl_df.append({
            'gl_account': acc[0],
            'account_description': acc[1],
            'account_group': acc[2],
            'account_type': acc[3],
            'profit_center_relevant': acc[2] in ['REVENUE', 'COGS', 'OPEX']
        })
    return pd.DataFrame(gl_df)

def create_employees(n=500):
    employees = []
    for i in range(n):
        hire_date = fake.date_between(start_date='-10y', end_date=start_date)
        employees.append({
            'employee_id': f'EMP{str(i+100000).zfill(6)}',
            'start_date': hire_date,
            'end_date': datetime(9999, 12, 31).date(),  # Active employees
            'employee_group': random.choice(['MGMT', 'SALES', 'TECH', 'ADMIN']),
            'employee_subgroup': random.choice(['MGR', 'SR', 'JR', 'LEAD']),
            'personnel_area': random.choice(['PA01', 'PA02', 'PA03']),
            'organizational_unit': f'ORG{random.randint(1000, 9999)}',
            'position': fake.job(),
            'job': random.choice(['MANAGER', 'ANALYST', 'SPECIALIST', 'COORDINATOR']),
            'cost_center': f'CC{random.randint(1000, 9999)}',
            'company_code': '1000'
        })
    return pd.DataFrame(employees)

# ===== TRANSACTIONAL DATA =====
def create_sales_orders(customers_df, materials_df, business_days):
    orders = []
    order_counter = 1
    
    for date in business_days:
        # Seasonal multiplier
        month = date.month
        if month in [11, 12]:  # Q4 boost
            daily_orders = random.randint(80, 120)
        elif month in [6, 7, 8]:  # Summer dip
            daily_orders = random.randint(30, 60)
        else:
            daily_orders = random.randint(50, 90)
        
        # Month-end boost
        if date.day >= 28:
            daily_orders = int(daily_orders * 1.3)
        
        for _ in range(daily_orders):
            customer = customers_df.sample(1).iloc[0]
            material = materials_df.sample(1).iloc[0]
            quantity = random.randint(1, 100)
            unit_price = material['standard_cost'] * random.uniform(1.2, 2.5)  # Markup
            
            orders.append({
                'sales_order_id': f'SO{str(order_counter).zfill(8)}',
                'item_number': '000010',
                'customer_id': customer['customer_id'],
                'material_id': material['material_id'],
                'order_date': date.date(),
                'requested_delivery_date': (date + timedelta(days=random.randint(7, 30))).date(),
                'order_quantity': quantity,
                'net_value': round(quantity * unit_price, 2),
                'currency': 'USD',
                'sales_org': random.choice(['SO01', 'SO02', 'SO03']),
                'plant': random.choice(['P001', 'P002', 'P003'])
            })
            order_counter += 1
    
    return pd.DataFrame(orders)

def create_billing_documents(sales_orders_df, business_days):
    billings = []
    billing_counter = 1
    
    # Create billing documents with 5-15 day lag from sales orders
    for _, order in sales_orders_df.iterrows():
        # Not all orders get billed immediately
        if random.random() < 0.85:  # 85% of orders get billed
            billing_delay = random.randint(5, 15)
            billing_date = pd.to_datetime(order['order_date']) + timedelta(days=billing_delay)
            
            # Only bill on business days
            while billing_date.weekday() >= 5:
                billing_date += timedelta(days=1)
            
            # Only if billing date is within our range
            if billing_date.date() <= end_date.date():
                tax_rate = 0.08  # 8% tax
                gross_value = order['net_value']
                tax_amount = round(gross_value * tax_rate, 2)
                
                billings.append({
                    'billing_document': f'BD{str(billing_counter).zfill(8)}',
                    'item_number': '000010',
                    'sales_order_id': order['sales_order_id'],
                    'customer_id': order['customer_id'],
                    'material_id': order['material_id'],
                    'billing_date': billing_date.date(),
                    'billing_quantity': order['order_quantity'],
                    'net_value': gross_value,
                    'tax_amount': tax_amount,
                    'gross_value': round(gross_value + tax_amount, 2),
                    'currency': order['currency'],
                    'cost_of_goods': round(gross_value * random.uniform(0.4, 0.7), 2)  # 40-70% COGS
                })
                billing_counter += 1
    
    return pd.DataFrame(billings)

def create_gl_line_items(billing_df, gl_accounts_df, business_days):
    gl_items = []
    gl_counter = 1
    doc_counter = 1
    
    # Revenue postings from billing
    for _, billing in billing_df.iterrows():
        doc_num = f'DOC{str(doc_counter).zfill(8)}'
        
        # Revenue posting
        gl_items.append({
            'id': gl_counter,
            'company_code': '1000',
            'gl_account': '4000000',  # Product Sales Revenue
            'posting_date': billing['billing_date'],
            'document_number': doc_num,
            'amount_local': billing['net_value'],
            'amount_group': billing['net_value'],
            'currency_local': 'USD',
            'currency_group': 'USD',
            'cost_center': f'CC{random.randint(1000, 9999)}',
            'profit_center': f'PC{random.randint(100, 999)}',
            'reference_doc': billing['billing_document'],
            'posting_period': billing['billing_date'].month if hasattr(billing['billing_date'], 'month') else pd.to_datetime(billing['billing_date']).month,
            'fiscal_year': billing['billing_date'].year if hasattr(billing['billing_date'], 'year') else pd.to_datetime(billing['billing_date']).year
        })
        gl_counter += 1
        
        # COGS posting
        gl_items.append({
            'id': gl_counter,
            'company_code': '1000',
            'gl_account': '5000000',  # COGS
            'posting_date': billing['billing_date'],
            'document_number': doc_num,
            'amount_local': -billing['cost_of_goods'],  # Negative for expense
            'amount_group': -billing['cost_of_goods'],
            'currency_local': 'USD',
            'currency_group': 'USD',
            'cost_center': f'CC{random.randint(1000, 9999)}',
            'profit_center': f'PC{random.randint(100, 999)}',
            'reference_doc': billing['billing_document'],
            'posting_period': billing['billing_date'].month if hasattr(billing['billing_date'], 'month') else pd.to_datetime(billing['billing_date']).month,
            'fiscal_year': billing['billing_date'].year if hasattr(billing['billing_date'], 'year') else pd.to_datetime(billing['billing_date']).year
        })
        gl_counter += 1
        doc_counter += 1
    
    # Additional operating expenses (monthly)
    monthly_dates = pd.date_range(start=start_date, end=end_date, freq='MS')  # Month start
    opex_accounts = ['6000000', '6010000', '6020000', '6030000']
    
    for month_date in monthly_dates:
        if month_date.weekday() < 5:  # Business day
            for account in opex_accounts:
                doc_num = f'DOC{str(doc_counter).zfill(8)}'
                amount = random.uniform(50000, 200000)  # Monthly expenses
                
                gl_items.append({
                    'id': gl_counter,
                    'company_code': '1000',
                    'gl_account': account,
                    'posting_date': month_date.date(),
                    'document_number': doc_num,
                    'amount_local': -amount,  # Negative for expense
                    'amount_group': -amount,
                    'currency_local': 'USD',
                    'currency_group': 'USD',
                    'cost_center': f'CC{random.randint(1000, 9999)}',
                    'profit_center': f'PC{random.randint(100, 999)}',
                    'reference_doc': f'ACCRUAL_{month_date.strftime("%Y%m")}',
                    'posting_period': month_date.month,
                    'fiscal_year': month_date.year
                })
                gl_counter += 1
                doc_counter += 1
    
    return pd.DataFrame(gl_items)

def create_copa_items(billing_df, customers_df, materials_df):
    copa_items = []
    copa_counter = 1
    
    for _, billing in billing_df.iterrows():
        customer = customers_df[customers_df['customer_id'] == billing['customer_id']].iloc[0]
        material = materials_df[materials_df['material_id'] == billing['material_id']].iloc[0]
        
        # Marketing cost allocation (roughly 5-10% of revenue)
        marketing_cost = billing['net_value'] * random.uniform(0.05, 0.10)
        sales_cost = billing['net_value'] * random.uniform(0.03, 0.08)
        
        copa_items.append({
            'id': copa_counter,
            'company_code': '1000',
            'operating_concern': 'OP01',
            'record_type': 'F',  # Actual
            'version': '0',
            'posting_period': billing['billing_date'].month if hasattr(billing['billing_date'], 'month') else pd.to_datetime(billing['billing_date']).month,
            'fiscal_year': billing['billing_date'].year if hasattr(billing['billing_date'], 'year') else pd.to_datetime(billing['billing_date']).year,
            'customer_id': billing['customer_id'],
            'material_id': billing['material_id'],
            'sales_org': random.choice(['SO01', 'SO02', 'SO03']),
            'product_line': material['product_line'],
            'revenue_amount': billing['net_value'],
            'cogs_amount': -billing['cost_of_goods'],
            'marketing_cost': -marketing_cost,
            'sales_cost': -sales_cost,
            'currency': 'USD',
            'posting_date': billing['billing_date']
        })
        copa_counter += 1
    
    return pd.DataFrame(copa_items)

def create_employee_actions(employees_df):
    actions = []
    action_counter = 1
    
    # Generate some turnover events
    for date in pd.date_range(start=start_date, end=end_date, freq='MS'):  # Monthly
        if date.weekday() < 5:  # Business day
            # Terminations (higher in Dec/Jan)
            if date.month in [12, 1]:
                num_terminations = random.randint(3, 8)
            else:
                num_terminations = random.randint(1, 4)
            
            # New hires (higher in Q1, Q3)
            if date.month in [1, 2, 3, 7, 8, 9]:
                num_hires = random.randint(4, 10)
            else:
                num_hires = random.randint(1, 5)
            
            # Terminations
            for _ in range(num_terminations):
                employee = employees_df.sample(1).iloc[0]
                actions.append({
                    'id': action_counter,
                    'employee_id': employee['employee_id'],
                    'action_type': 'TERMINATE',
                    'action_date': date.date(),
                    'action_reason': random.choice(['RESIGNATION', 'LAYOFF', 'RETIREMENT', 'PERFORMANCE']),
                    'organizational_unit_old': employee['organizational_unit'],
                    'organizational_unit_new': None,
                    'position_old': employee['position'],
                    'position_new': None
                })
                action_counter += 1
            
            # New hires
            for _ in range(num_hires):
                actions.append({
                    'id': action_counter,
                    'employee_id': f'EMP{str(random.randint(200000, 299999)).zfill(6)}',
                    'action_type': 'HIRE',
                    'action_date': date.date(),
                    'action_reason': 'NEW_HIRE',
                    'organizational_unit_old': None,
                    'organizational_unit_new': f'ORG{random.randint(1000, 9999)}',
                    'position_old': None,
                    'position_new': fake.job()
                })
                action_counter += 1
    
    return pd.DataFrame(actions)

# Generate all datasets
print("Creating master data...")
dim_date_df = create_date_dimension()
customers_df = create_customers(50)
materials_df = create_materials(200)
gl_accounts_df = create_gl_accounts()
employees_df = create_employees(500)

print("Creating customer sales data...")
knvv_df = customers_df.copy()
knvv_df['sales_org'] = knvv_df.apply(lambda x: random.choice(['SO01', 'SO02', 'SO03']), axis=1)
knvv_df['distribution_channel'] = knvv_df.apply(lambda x: random.choice(['DC01', 'DC02']), axis=1)
knvv_df['division'] = knvv_df.apply(lambda x: random.choice(['DIV01', 'DIV02', 'DIV03']), axis=1)
knvv_df['customer_classification'] = knvv_df.apply(lambda x: random.choice(['A', 'B', 'C']), axis=1)
knvv_df['payment_terms'] = knvv_df.apply(lambda x: random.choice(['NET30', 'NET60', 'COD']), axis=1)
knvv_df['sales_rep'] = knvv_df.apply(lambda x: f'REP{random.randint(1001, 1099)}', axis=1)

print("Creating transactional data...")
print("- Sales orders...")
sales_orders_df = create_sales_orders(customers_df, materials_df, business_days)
print(f"  Generated {len(sales_orders_df)} sales orders")

print("- Billing documents...")
billing_df = create_billing_documents(sales_orders_df, business_days)
print(f"  Generated {len(billing_df)} billing documents")

print("- GL line items...")
gl_items_df = create_gl_line_items(billing_df, gl_accounts_df, business_days)
print(f"  Generated {len(gl_items_df)} GL line items")

print("- CO-PA items...")
copa_df = create_copa_items(billing_df, customers_df, materials_df)
print(f"  Generated {len(copa_df)} CO-PA records")

print("- Employee actions...")
employee_actions_df = create_employee_actions(employees_df)
print(f"  Generated {len(employee_actions_df)} employee actions")

# Create document headers
doc_headers = []
for doc_num in gl_items_df['document_number'].unique():
    gl_doc = gl_items_df[gl_items_df['document_number'] == doc_num].iloc[0]
    doc_headers.append({
        'document_number': doc_num,
        'company_code': gl_doc['company_code'],
        'document_date': gl_doc['posting_date'],
        'posting_date': gl_doc['posting_date'],
        'document_type': 'SA',  # Sales document
        'reference': gl_doc['reference_doc'],
        'currency': gl_doc['currency_local'],
        'exchange_rate': 1.0
    })

doc_headers_df = pd.DataFrame(doc_headers)

# Save all datasets
datasets = {
    'dim_date': dim_date_df,
    'kna1_customers': customers_df,
    'knvv_customer_sales': knvv_df,
    'mara_materials': materials_df,
    'skat_gl_accounts': gl_accounts_df,
    'pa0001_hr_master': employees_df,
    'vbap_sales_orders': sales_orders_df,
    'vbrp_billing': billing_df,
    'faglflexa_gl_items': gl_items_df,
    'bkpf_doc_header': doc_headers_df,
    'coep_copa_items': copa_df,
    'pa0000_employee_actions': employee_actions_df
}

print("\nSaving datasets to CSV files...")
for name, df in datasets.items():
    filename = f'{name}.csv'
    df.to_csv(filename, index=False)
    print(f"Saved {filename} - {len(df)} records")

print(f"\nData generation complete!")
print(f"Date range: {start_date.date()} to {end_date.date()}")
print(f"Business days: {len(business_days)}")
print(f"Total sales orders: {len(sales_orders_df):,}")
print(f"Total billing documents: {len(billing_df):,}")
print(f"Total GL postings: {len(gl_items_df):,}")

# Quick data quality check
print("\n=== DATA QUALITY SUMMARY ===")
print(f"Revenue total: ${billing_df['net_value'].sum():,.2f}")
print(f"COGS total: ${billing_df['cost_of_goods'].sum():,.2f}")
print(f"Gross margin: {((billing_df['net_value'].sum() - billing_df['cost_of_goods'].sum()) / billing_df['net_value'].sum() * 100):.1f}%")
print(f"Active customers: {customers_df['customer_id'].nunique()}")
print(f"Active materials: {materials_df['material_id'].nunique()}")
print(f"Employee actions: {employee_actions_df['action_type'].value_counts().to_dict()}")