import pyodbc

conn_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\\MSSQLLocalDB;"
    "DATABASE=BerthPlanning;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT COUNT(*) FROM VESSELS")
    count = cursor.fetchone()[0]
    print(f"Database Connection: SUCCESS")
    print(f"Vessels in database: {count}")
    
    # Test another table
    cursor.execute("SELECT COUNT(*) FROM BERTHS")
    berth_count = cursor.fetchone()[0]
    print(f"Berths in database: {berth_count}")
    
    conn.close()
    print("Connection closed successfully")
except Exception as e:
    print(f"Error: {e}")
