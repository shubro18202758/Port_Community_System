import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'Server=20.204.224.123,1433;'
    'Database=BerthPlanning;'
    'UID=Admin;'
    'PWD=Adm!n#@@7;'
    'TrustServerCertificate=Yes;'
)
cursor = conn.cursor()

# Get all check constraints
cursor.execute("SELECT name, definition FROM sys.check_constraints")
print("CHECK Constraints:")
for r in cursor.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Check CSV status values
import pandas as pd
csv_path = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\documents\Data\Mundra\VESSEL_SCHEDULE.csv"
df = pd.read_csv(csv_path)
print("\nCSV Status values (unique):")
print(df['status'].unique())

conn.close()
