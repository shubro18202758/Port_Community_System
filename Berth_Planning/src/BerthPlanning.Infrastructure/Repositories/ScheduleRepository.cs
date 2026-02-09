using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class ScheduleRepository : IScheduleRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public ScheduleRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<VesselSchedule>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.PredictedETA, vs.ETD,
                   vs.ATA, vs.ATB, vs.ATD, vs.Status, vs.DwellTime, vs.WaitingTime,
                   vs.OptimizationScore, vs.IsOptimized, vs.ConflictCount, vs.CreatedAt, vs.UpdatedAt,
                   v.VesselName, v.VesselType, b.BerthName
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            ORDER BY vs.ETA";
        return await connection.QueryAsync<VesselSchedule>(sql);
    }

    public async Task<IEnumerable<VesselSchedule>> GetActiveAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.PredictedETA, vs.ETD,
                   vs.ATA, vs.ATB, vs.ATD, vs.Status, vs.DwellTime, vs.WaitingTime,
                   vs.OptimizationScore, vs.IsOptimized, vs.ConflictCount, vs.CreatedAt, vs.UpdatedAt,
                   v.VesselName, v.VesselType, b.BerthName
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.Status NOT IN ('Departed', 'Cancelled')
            ORDER BY vs.ETA";
        return await connection.QueryAsync<VesselSchedule>(sql);
    }

    public async Task<IEnumerable<VesselSchedule>> GetByStatusAsync(string status)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.PredictedETA, vs.ETD,
                   vs.ATA, vs.ATB, vs.ATD, vs.Status, vs.DwellTime, vs.WaitingTime,
                   vs.OptimizationScore, vs.IsOptimized, vs.ConflictCount, vs.CreatedAt, vs.UpdatedAt,
                   v.VesselName, v.VesselType, b.BerthName
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.Status = @Status
            ORDER BY vs.ETA";
        return await connection.QueryAsync<VesselSchedule>(sql, new { Status = status });
    }

    public async Task<IEnumerable<VesselSchedule>> GetByBerthAsync(int berthId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.PredictedETA, vs.ETD,
                   vs.ATA, vs.ATB, vs.ATD, vs.Status, vs.DwellTime, vs.WaitingTime,
                   vs.OptimizationScore, vs.IsOptimized, vs.ConflictCount, vs.CreatedAt, vs.UpdatedAt,
                   v.VesselName, v.VesselType, b.BerthName
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.BerthId = @BerthId AND vs.Status NOT IN ('Departed', 'Cancelled')
            ORDER BY vs.ETA";
        return await connection.QueryAsync<VesselSchedule>(sql, new { BerthId = berthId });
    }

    public async Task<IEnumerable<VesselSchedule>> GetByDateRangeAsync(DateTime startDate, DateTime endDate)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.PredictedETA, vs.ETD,
                   vs.ATA, vs.ATB, vs.ATD, vs.Status, vs.DwellTime, vs.WaitingTime,
                   vs.OptimizationScore, vs.IsOptimized, vs.ConflictCount, vs.CreatedAt, vs.UpdatedAt,
                   v.VesselName, v.VesselType, b.BerthName
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE (vs.ETA BETWEEN @StartDate AND @EndDate)
               OR (vs.ETD BETWEEN @StartDate AND @EndDate)
               OR (vs.ETA <= @StartDate AND vs.ETD >= @EndDate)
            ORDER BY vs.ETA";
        return await connection.QueryAsync<VesselSchedule>(sql, new { StartDate = startDate, EndDate = endDate });
    }

    public async Task<VesselSchedule?> GetByIdAsync(int scheduleId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.PredictedETA, vs.ETD,
                   vs.ATA, vs.ATB, vs.ATD, vs.Status, vs.DwellTime, vs.WaitingTime,
                   vs.OptimizationScore, vs.IsOptimized, vs.ConflictCount, vs.CreatedAt, vs.UpdatedAt,
                   v.VesselName, v.VesselType, b.BerthName
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.ScheduleId = @ScheduleId";
        return await connection.QueryFirstOrDefaultAsync<VesselSchedule>(sql, new { ScheduleId = scheduleId });
    }

    public async Task<VesselSchedule?> GetByVesselIdAsync(int vesselId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT TOP 1 vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.PredictedETA, vs.ETD,
                   vs.ATA, vs.ATB, vs.ATD, vs.Status, vs.DwellTime, vs.WaitingTime,
                   vs.OptimizationScore, vs.IsOptimized, vs.ConflictCount, vs.CreatedAt, vs.UpdatedAt,
                   v.VesselName, v.VesselType, b.BerthName
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.VesselId = @VesselId AND vs.Status NOT IN ('Departed', 'Cancelled')
            ORDER BY vs.ETA DESC";
        return await connection.QueryFirstOrDefaultAsync<VesselSchedule>(sql, new { VesselId = vesselId });
    }

    public async Task<AllocationResultDto> AllocateVesselToBerthAsync(int vesselId, int berthId, DateTime eta, DateTime etd, int? dwellTime)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        try
        {
            DynamicParameters parameters = new();
            parameters.Add("@VesselId", vesselId);
            parameters.Add("@BerthId", berthId);
            parameters.Add("@ETA", eta);
            parameters.Add("@ETD", etd);
            parameters.Add("@DwellTime", dwellTime);
            parameters.Add("@ScheduleId", dbType: DbType.Int32, direction: ParameterDirection.Output);

            _ = await connection.ExecuteAsync("sp_AllocateVesselToBerth", parameters, commandType: CommandType.StoredProcedure);

            var scheduleId = parameters.Get<int?>("@ScheduleId");

            return new AllocationResultDto
            {
                Success = scheduleId.HasValue,
                ScheduleId = scheduleId,
                Message = scheduleId.HasValue ? "Vessel allocated successfully" : "Allocation failed"
            };
        }
        catch (Exception ex)
        {
            return new AllocationResultDto
            {
                Success = false,
                Message = ex.Message
            };
        }
    }

    public async Task<bool> UpdateVesselETAAsync(int scheduleId, DateTime newETA, DateTime? newPredictedETA)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        var result = await connection.ExecuteAsync(
            "sp_UpdateVesselETA",
            new { ScheduleId = scheduleId, NewETA = newETA, NewPredictedETA = newPredictedETA },
            commandType: CommandType.StoredProcedure);
        return result > 0;
    }

    public async Task<bool> RecordVesselArrivalAsync(int scheduleId, DateTime ata)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        var result = await connection.ExecuteAsync(
            "sp_RecordVesselArrival",
            new { ScheduleId = scheduleId, ATA = ata },
            commandType: CommandType.StoredProcedure);
        return result > 0;
    }

    public async Task<bool> RecordVesselBerthingAsync(int scheduleId, DateTime atb)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        var result = await connection.ExecuteAsync(
            "sp_RecordVesselBerthing",
            new { ScheduleId = scheduleId, ATB = atb },
            commandType: CommandType.StoredProcedure);
        return result > 0;
    }

    public async Task<bool> RecordVesselDepartureAsync(int scheduleId, DateTime atd)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        var result = await connection.ExecuteAsync(
            "sp_RecordVesselDeparture",
            new { ScheduleId = scheduleId, ATD = atd },
            commandType: CommandType.StoredProcedure);
        return result > 0;
    }

    public async Task<int> CreateAsync(VesselSchedule schedule)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, DwellTime, Status)
            VALUES (@VesselId, @BerthId, @ETA, @PredictedETA, @ETD, @DwellTime, @Status);
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.QuerySingleAsync<int>(sql, schedule);
    }

    public async Task<bool> UpdateAsync(VesselSchedule schedule)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE VESSEL_SCHEDULE SET
                BerthId = @BerthId,
                ETA = @ETA,
                PredictedETA = @PredictedETA,
                ETD = @ETD,
                ATA = @ATA,
                ATB = @ATB,
                ATD = @ATD,
                Status = @Status,
                DwellTime = @DwellTime,
                WaitingTime = @WaitingTime,
                OptimizationScore = @OptimizationScore,
                IsOptimized = @IsOptimized,
                ConflictCount = @ConflictCount,
                UpdatedAt = GETUTCDATE()
            WHERE ScheduleId = @ScheduleId";
        var rowsAffected = await connection.ExecuteAsync(sql, schedule);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(int scheduleId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM VESSEL_SCHEDULE WHERE ScheduleId = @ScheduleId";
        var rowsAffected = await connection.ExecuteAsync(sql, new { ScheduleId = scheduleId });
        return rowsAffected > 0;
    }
}
