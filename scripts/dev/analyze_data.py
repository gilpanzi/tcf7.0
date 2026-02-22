import sqlite3
import pandas as pd
import os

db_path = r'c:\Basidh\tcf7.0\tcf7.0\data\fan_pricing.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Analyze Enquiry Register
print("--- Enquiry Register Analysis ---")
df_enq = pd.read_sql_query("SELECT * FROM EnquiryRegister", conn)
print(f"Total Enquiries in Register: {len(df_enq)}")
if not df_enq.empty:
    print("\nEnquiries by Year:")
    print(df_enq['year'].value_counts())
    print("\nTop 5 Sales Engineers by Enquiries:")
    print(df_enq['sales_engineer'].value_counts().head(5))

# Analyze Orders
print("\n--- Orders Analysis ---")
df_orders = pd.read_sql_query("SELECT * FROM Orders", conn)
print(f"Total Orders: {len(df_orders)}")
if not df_orders.empty:
    print("\nOrders by Year:")
    print(df_orders['year'].value_counts())
    print("\nTotal Order Value by Region (Top 5):")
    if 'region' in df_orders.columns and 'order_value' in df_orders.columns:
        print(df_orders.groupby('region')['order_value'].sum().sort_values(ascending=False).head(5))

# Analyze Projects (Current Pipeline)
print("\n--- Current Pipeline Analysis ---")
df_proj = pd.read_sql_query("SELECT * FROM Projects", conn)
print(f"Total Projects in Pipeline: {len(df_proj)}")
if not df_proj.empty:
    print("\nProjects by Status:")
    print(df_proj['status'].value_counts())

conn.close()
