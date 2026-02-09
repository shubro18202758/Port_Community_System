# BERTH PLANNING & ALLOCATION OPTIMIZATION SYSTEM
## SQL Database Scripts - Complete Guide

---

## 📦 **PACKAGE CONTENTS**

This package contains all SQL scripts needed to set up and operate the Berth Planning database:

### **1. Schema Scripts**
- `01_Create_Tables_MSSQL.sql` - Complete database schema (16 tables)
- `02_Insert_Sample_Data.sql` - Sample data for testing
- `03_Create_Views.sql` - 11 pre-built views for common queries
- `04_Create_StoredProcedures.sql` - 8 stored procedures for operations

### **2. Documentation**
- `ERD_Documentation.md` - Detailed entity relationship documentation
- `berth_planning_erd.html` - Visual ERD diagram (open in browser)
- `berth_planning_erd.mermaid` - ERD for documentation tools
- `README_SQL_Scripts.md` - This file

---

## 🚀 **QUICK START GUIDE**

### **Step 1: Create Database**
```sql
-- In SQL Server Management Studio (SSMS)
CREATE DATABASE BerthPlanningDB;
GO

USE BerthPlanningDB;
GO
```

### **Step 2: Run Scripts in Order**

**Order is important!**

```sql
-- 1. Create all tables
:r 01_Create_Tables_MSSQL.sql

-- 2. Insert sample data (optional but recommended for testing)
:r 02_Insert_Sample_Data.sql

-- 3. Create views
:r 03_Create_Views.sql

-- 4. Create stored procedures
:r 04_Create_StoredProcedures.sql
```

**Alternative (using PowerShell):**
```powershell
# Set connection string
$serverInstance = "localhost\SQLEXPRESS"
$database = "BerthPlanningDB"

# Run scripts
Invoke-Sqlcmd -ServerInstance $serverInstance -Database $database -InputFile "01_Create_Tables_MSSQL.sql"
Invoke-Sqlcmd -ServerInstance $serverInstance -Database $database -InputFile "02_Insert_Sample_Data.sql"
Invoke-Sqlcmd -ServerInstance $serverInstance -Database $database -InputFile "03_Create_Views.sql"
Invoke-Sqlcmd -ServerInstance $serverInstance -Database $database -InputFile "04_Create_StoredProcedures.sql"
```

### **Step 3: Verify Installation**
```sql
-- Check table count
SELECT COUNT(*) AS TableCount
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE';
-- Expected: 16 tables

-- Check view count
SELECT COUNT(*) AS ViewCount
FROM INFORMATION_SCHEMA.VIEWS;
-- Expected: 11 views

-- Check stored procedure count
SELECT COUNT(*) AS ProcedureCount
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_TYPE = 'PROCEDURE';
-- Expected: 8 procedures

-- Get dashboard metrics (will work if sample data loaded)
EXEC sp_GetDashboardStats;
```

---

## 📊 **DATABASE SCHEMA OVERVIEW**

### **16 Tables Organized by Category**

#### **Core Entities (2 tables)**
- `VESSELS` - Ship master data (10 sample records)
- `BERTHS` - Berth location data (10 sample records)

#### **Operational Data (3 tables)**
- `VESSEL_SCHEDULE` - Central scheduling table (10 sample records)
- `RESOURCES` - Port resources (16 sample records: cranes, pilots, tugboats)
- `RESOURCE_ALLOCATION` - Resource assignments

#### **External Data (3 tables)**
- `WEATHER_DATA` - Weather from APIs (48 sample records)
- `TIDAL_DATA` - Tidal schedules (28 sample records)
- `AIS_DATA` - Vessel tracking (3 sample records)

#### **AI/ML Entities (3 tables)**
- `CONFLICTS` - Detected conflicts (1 sample record)
- `OPTIMIZATION_RUNS` - Optimization history (1 sample record)
- `KNOWLEDGE_BASE` - RAG documents (3 sample records)

#### **Support Tables (5 tables)**
- `VESSEL_HISTORY` - Historical visits (5 sample records)
- `BERTH_MAINTENANCE` - Maintenance schedules (2 sample records)
- `ALERTS_NOTIFICATIONS` - System alerts (3 sample records)
- `USER_PREFERENCES` - User settings
- `AUDIT_LOG` - Audit trail

---

## 🔍 **KEY VIEWS QUICK REFERENCE**

### **Dashboard Views**
```sql
-- Real-time berth status
SELECT * FROM vw_CurrentBerthStatus;

-- Vessel queue and metrics
SELECT * FROM vw_VesselQueueDashboard 
WHERE Status = 'Approaching'
ORDER BY MinutesUntilArrival;

-- Dashboard KPIs
SELECT * FROM vw_DashboardMetrics;

-- Current weather
SELECT * FROM vw_CurrentWeather;
```

### **Planning Views**
```sql
-- Gantt chart data for timeline
SELECT * FROM vw_BerthTimeline
WHERE StartTime >= CAST(GETDATE() AS DATE)
ORDER BY BerthId, StartTime;

-- Find compatible berths for a vessel
EXEC sp_FindCompatibleBerths 
    @VesselId = 1, 
    @ETA = '2025-02-01 10:00:00',
    @DwellTime = 360;

-- Check specific berth availability
EXEC sp_CheckBerthAvailability
    @BerthId = 1,
    @StartTime = '2025-02-01 10:00:00',
    @EndTime = '2025-02-01 16:00:00';
```

### **Monitoring Views**
```sql
-- Active conflicts
SELECT * FROM vw_ActiveConflicts
ORDER BY Severity, DetectedAt;

-- Resource utilization
SELECT * FROM vw_ResourceUtilization
WHERE ResourceType = 'Crane';

-- Latest vessel positions
SELECT * FROM vw_LatestVesselPositions
WHERE ScheduleStatus = 'Approaching';
```

### **Analytics Views**
```sql
-- Vessel performance history
SELECT * FROM vw_VesselPerformanceHistory
WHERE TotalVisits > 0
ORDER BY AvgWaitingTime DESC;

-- Berth performance metrics
SELECT * FROM vw_BerthPerformanceMetrics
ORDER BY UtilizationRate DESC;
```

---

## 💼 **COMMON STORED PROCEDURES**

### **1. Allocate Vessel to Berth**
```sql
DECLARE @NewScheduleId INT;

EXEC sp_AllocateVesselToBerth
    @VesselId = 1,
    @BerthId = 2,
    @ETA = '2025-02-01 14:00:00',
    @ETD = '2025-02-01 20:00:00',
    @Priority = 1,
    @DwellTime = 360,
    @ScheduleId = @NewScheduleId OUTPUT;

SELECT @NewScheduleId AS CreatedScheduleId;
```

### **2. Update Vessel ETA**
```sql
EXEC sp_UpdateVesselETA
    @ScheduleId = 1,
    @NewETA = '2025-02-01 14:30:00',
    @NewPredictedETA = '2025-02-01 14:25:00',
    @Reason = 'Weather delay - high winds';
```

### **3. Record Vessel Arrival**
```sql
EXEC sp_RecordVesselArrival
    @ScheduleId = 1,
    @ActualArrivalTime = '2025-02-01 14:35:00';
```

### **4. Record Vessel Berthing**
```sql
EXEC sp_RecordVesselBerthing
    @ScheduleId = 1,
    @BerthingTime = '2025-02-01 15:00:00';
```

### **5. Record Vessel Departure**
```sql
EXEC sp_RecordVesselDeparture
    @ScheduleId = 1,
    @DepartureTime = '2025-02-01 20:30:00';
```

### **6. Get Dashboard Statistics**
```sql
-- Complete dashboard stats
EXEC sp_GetDashboardStats;
```

---

## 🔧 **ENTITY FRAMEWORK CORE INTEGRATION**

### **Generate Models from Database**

**Option 1: Scaffold entire database**
```bash
dotnet ef dbcontext scaffold "Server=localhost;Database=BerthPlanningDB;Trusted_Connection=True;" Microsoft.EntityFrameworkCore.SqlServer -o Models
```

**Option 2: Scaffold specific tables**
```bash
dotnet ef dbcontext scaffold "Server=localhost;Database=BerthPlanningDB;Trusted_Connection=True;" Microsoft.EntityFrameworkCore.SqlServer -o Models -t VESSELS -t BERTHS -t VESSEL_SCHEDULE
```

### **Sample Connection String (appsettings.json)**
```json
{
  "ConnectionStrings": {
    "BerthPlanningDb": "Server=localhost;Database=BerthPlanningDB;Trusted_Connection=True;TrustServerCertificate=True;"
  }
}
```

### **DbContext Configuration (C#)**
```csharp
public class BerthPlanningContext : DbContext
{
    public BerthPlanningContext(DbContextOptions<BerthPlanningContext> options)
        : base(options)
    {
    }

    // DbSets
    public DbSet<Vessel> Vessels { get; set; }
    public DbSet<Berth> Berths { get; set; }
    public DbSet<VesselSchedule> VesselSchedules { get; set; }
    public DbSet<Resource> Resources { get; set; }
    public DbSet<ResourceAllocation> ResourceAllocations { get; set; }
    // ... add all tables

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Configure relationships if needed
        modelBuilder.Entity<VesselSchedule>()
            .HasOne(vs => vs.Vessel)
            .WithMany(v => v.Schedules)
            .HasForeignKey(vs => vs.VesselId);
            
        modelBuilder.Entity<VesselSchedule>()
            .HasOne(vs => vs.Berth)
            .WithMany(b => b.Schedules)
            .HasForeignKey(vs => vs.BerthId);
    }
}
```

### **Startup Configuration (Program.cs)**
```csharp
builder.Services.AddDbContext<BerthPlanningContext>(options =>
    options.UseSqlServer(
        builder.Configuration.GetConnectionString("BerthPlanningDb")
    )
);
```

---

## 📈 **SAMPLE QUERIES FOR TESTING**

### **1. Get Today's Schedule**
```sql
SELECT 
    v.VesselName,
    b.BerthName,
    vs.ETA,
    vs.ETD,
    vs.Status,
    vs.DwellTime
FROM VESSEL_SCHEDULE vs
INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
INNER JOIN BERTHS b ON vs.BerthId = b.BerthId
WHERE CAST(vs.ETA AS DATE) = CAST(GETDATE() AS DATE)
ORDER BY vs.ETA;
```

### **2. Find Available Berths Right Now**
```sql
SELECT 
    b.BerthId,
    b.BerthName,
    b.BerthType,
    b.NumberOfCranes,
    'Available Now' AS Status
FROM BERTHS b
WHERE b.IsActive = 1
    AND NOT EXISTS (
        SELECT 1 FROM VESSEL_SCHEDULE vs
        WHERE vs.BerthId = b.BerthId
            AND vs.Status = 'Berthed'
    )
    AND NOT EXISTS (
        SELECT 1 FROM BERTH_MAINTENANCE bm
        WHERE bm.BerthId = b.BerthId
            AND bm.Status = 'InProgress'
    );
```

### **3. Get Resource Allocation for Today**
```sql
SELECT 
    r.ResourceType,
    r.ResourceName,
    v.VesselName,
    b.BerthName,
    ra.AllocatedFrom,
    ra.AllocatedTo,
    ra.Status
FROM RESOURCE_ALLOCATION ra
INNER JOIN RESOURCES r ON ra.ResourceId = r.ResourceId
INNER JOIN VESSEL_SCHEDULE vs ON ra.ScheduleId = vs.ScheduleId
INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
INNER JOIN BERTHS b ON vs.BerthId = b.BerthId
WHERE CAST(ra.AllocatedFrom AS DATE) = CAST(GETDATE() AS DATE)
ORDER BY r.ResourceType, ra.AllocatedFrom;
```

### **4. Calculate Berth Utilization (Last 7 Days)**
```sql
SELECT 
    b.BerthName,
    COUNT(vs.ScheduleId) AS VesselsServed,
    SUM(vs.DwellTime) AS TotalMinutesOccupied,
    SUM(vs.DwellTime) / 60.0 AS TotalHoursOccupied,
    (SUM(vs.DwellTime) / (7.0 * 24.0 * 60.0)) * 100 AS UtilizationPercent
FROM BERTHS b
LEFT JOIN VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId
    AND vs.Status = 'Departed'
    AND vs.ATD >= DATEADD(DAY, -7, GETDATE())
WHERE b.IsActive = 1
GROUP BY b.BerthId, b.BerthName
ORDER BY UtilizationPercent DESC;
```

### **5. Find Vessels with Delays**
```sql
SELECT 
    v.VesselName,
    vs.ETA AS ScheduledETA,
    vs.ATA AS ActualArrival,
    DATEDIFF(MINUTE, vs.ETA, vs.ATA) AS DelayMinutes,
    vs.WaitingTime,
    b.BerthName
FROM VESSEL_SCHEDULE vs
INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
WHERE vs.ATA > vs.ETA
    AND vs.Status = 'Departed'
    AND vs.ATD >= DATEADD(DAY, -30, GETDATE())
ORDER BY DelayMinutes DESC;
```

---

## 🛠️ **MAINTENANCE TASKS**

### **Cleanup Old Data**
```sql
-- Archive old AIS data (keep last 90 days)
DELETE FROM AIS_DATA
WHERE RecordedAt < DATEADD(DAY, -90, GETDATE());

-- Archive old weather data (keep last 1 year)
DELETE FROM WEATHER_DATA
WHERE RecordedAt < DATEADD(YEAR, -1, GETDATE());

-- Archive completed schedules (keep last 1 year)
DELETE FROM VESSEL_SCHEDULE
WHERE Status = 'Departed'
    AND ATD < DATEADD(YEAR, -1, GETDATE());
```

### **Update Statistics**
```sql
-- Update statistics for better query performance
UPDATE STATISTICS VESSELS;
UPDATE STATISTICS BERTHS;
UPDATE STATISTICS VESSEL_SCHEDULE;
UPDATE STATISTICS RESOURCE_ALLOCATION;
UPDATE STATISTICS AIS_DATA;
```

### **Rebuild Indexes**
```sql
-- Rebuild fragmented indexes
ALTER INDEX ALL ON VESSEL_SCHEDULE REBUILD;
ALTER INDEX ALL ON AIS_DATA REBUILD;
ALTER INDEX ALL ON RESOURCE_ALLOCATION REBUILD;
```

---

## 🔒 **SECURITY RECOMMENDATIONS**

### **Create Application User**
```sql
-- Create login
CREATE LOGIN BerthPlanningApp WITH PASSWORD = 'YourSecurePassword123!';

-- Create user
USE BerthPlanningDB;
CREATE USER BerthPlanningApp FOR LOGIN BerthPlanningApp;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON dbo.VESSELS TO BerthPlanningApp;
GRANT SELECT, INSERT, UPDATE ON dbo.BERTHS TO BerthPlanningApp;
GRANT SELECT, INSERT, UPDATE ON dbo.VESSEL_SCHEDULE TO BerthPlanningApp;
GRANT SELECT, INSERT, UPDATE ON dbo.RESOURCES TO BerthPlanningApp;
GRANT SELECT, INSERT, UPDATE ON dbo.RESOURCE_ALLOCATION TO BerthPlanningApp;
GRANT SELECT, INSERT ON dbo.AUDIT_LOG TO BerthPlanningApp;

-- Grant execute on stored procedures
GRANT EXECUTE ON sp_AllocateVesselToBerth TO BerthPlanningApp;
GRANT EXECUTE ON sp_UpdateVesselETA TO BerthPlanningApp;
GRANT EXECUTE ON sp_RecordVesselArrival TO BerthPlanningApp;
GRANT EXECUTE ON sp_RecordVesselBerthing TO BerthPlanningApp;
GRANT EXECUTE ON sp_RecordVesselDeparture TO BerthPlanningApp;
GRANT EXECUTE ON sp_GetDashboardStats TO BerthPlanningApp;
```

### **Read-Only User for Analytics**
```sql
CREATE LOGIN BerthAnalytics WITH PASSWORD = 'YourSecurePassword456!';

USE BerthPlanningDB;
CREATE USER BerthAnalytics FOR LOGIN BerthAnalytics;

-- Grant read-only access
GRANT SELECT ON SCHEMA::dbo TO BerthAnalytics;
```

---

## 📞 **TROUBLESHOOTING**

### **Issue: Foreign Key Constraint Errors**
```sql
-- Check for orphaned records
SELECT vs.* 
FROM VESSEL_SCHEDULE vs
LEFT JOIN VESSELS v ON vs.VesselId = v.VesselId
WHERE v.VesselId IS NULL;

SELECT vs.* 
FROM VESSEL_SCHEDULE vs
LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
WHERE vs.BerthId IS NOT NULL AND b.BerthId IS NULL;
```

### **Issue: Slow Queries**
```sql
-- Check missing indexes
SELECT 
    OBJECT_NAME(ips.object_id) AS TableName,
    ips.avg_user_impact,
    ips.avg_total_user_cost,
    ips.user_seeks + ips.user_scans AS TotalSeeks
FROM sys.dm_db_missing_index_group_stats AS igs
INNER JOIN sys.dm_db_missing_index_groups AS ig ON igs.group_handle = ig.index_group_handle
INNER JOIN sys.dm_db_missing_index_details AS ips ON ig.index_handle = ips.index_handle
ORDER BY ips.avg_user_impact DESC;
```

### **Issue: Data Conflicts**
```sql
-- Find overlapping schedules
SELECT 
    vs1.ScheduleId AS Schedule1,
    vs1.VesselId AS Vessel1,
    vs1.ETA AS ETA1,
    vs1.ETD AS ETD1,
    vs2.ScheduleId AS Schedule2,
    vs2.VesselId AS Vessel2,
    vs2.ETA AS ETA2,
    vs2.ETD AS ETD2
FROM VESSEL_SCHEDULE vs1
INNER JOIN VESSEL_SCHEDULE vs2 ON vs1.BerthId = vs2.BerthId
    AND vs1.ScheduleId < vs2.ScheduleId
WHERE vs1.Status IN ('Scheduled', 'Approaching', 'Berthed')
    AND vs2.Status IN ('Scheduled', 'Approaching', 'Berthed')
    AND vs1.ETA <= vs2.ETD
    AND vs1.ETD >= vs2.ETA;
```

---

## 📚 **NEXT STEPS**

After setting up the database:

1. ✅ **Test with Sample Data**
   - Run sample queries
   - Test stored procedures
   - Verify views return data

2. ✅ **Configure Entity Framework**
   - Generate models
   - Set up DbContext
   - Test CRUD operations

3. ✅ **Build .NET API**
   - Create controllers using models
   - Implement business logic
   - Add validation

4. ✅ **Integrate External APIs**
   - Weather API → populate WEATHER_DATA
   - AIS API → populate AIS_DATA
   - Tidal API → populate TIDAL_DATA

5. ✅ **Implement AI/ML Agents**
   - ETA Predictor → update PredictedETA
   - Berth Optimizer → create OPTIMIZATION_RUNS
   - Conflict Resolver → create CONFLICTS

6. ✅ **Build Frontend**
   - Dashboard using views
   - Gantt chart from vw_BerthTimeline
   - Real-time updates via SignalR

---

## 📝 **CHANGE LOG**

**Version 1.0 - 2025-01-31**
- Initial release
- 16 tables created
- 11 views implemented
- 8 stored procedures added
- Sample data included
- Full documentation provided

---

## 🆘 **SUPPORT**

For questions or issues:
1. Review the ERD_Documentation.md file
2. Check sample queries in this README
3. Consult the views and stored procedures
4. Review table definitions in 01_Create_Tables_MSSQL.sql

---

**Happy Coding! 🚢⚓**
