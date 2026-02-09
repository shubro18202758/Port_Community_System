using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class PilotRepository : IPilotRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public PilotRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<Pilot>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT * FROM PILOTS
            ORDER BY PilotName";
        return await connection.QueryAsync<Pilot>(sql);
    }

    public async Task<Pilot?> GetByIdAsync(int pilotId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "SELECT * FROM PILOTS WHERE PilotId = @PilotId";
        return await connection.QueryFirstOrDefaultAsync<Pilot>(sql, new { PilotId = pilotId });
    }

    public async Task<IEnumerable<Pilot>> GetByPortCodeAsync(string portCode)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT * FROM PILOTS
            WHERE PortCode = @PortCode
            ORDER BY PilotName";
        return await connection.QueryAsync<Pilot>(sql, new { PortCode = portCode });
    }

    public async Task<IEnumerable<Pilot>> GetByTypeAsync(string pilotType)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT * FROM PILOTS
            WHERE PilotType = @PilotType
            ORDER BY PilotName";
        return await connection.QueryAsync<Pilot>(sql, new { PilotType = pilotType });
    }

    public async Task<IEnumerable<Pilot>> GetByStatusAsync(string status)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT * FROM PILOTS
            WHERE Status = @Status
            ORDER BY PilotName";
        return await connection.QueryAsync<Pilot>(sql, new { Status = status });
    }

    public async Task<int> CreateAsync(Pilot pilot)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO PILOTS (PortCode, PortName, PilotName, PilotCode, PilotType,
                PilotClass, CertificationLevel, ExperienceYears, MaxVesselGT, MaxVesselLOA,
                NightOperations, AdverseWeather, CanTrain, LicenseIssueDate, LicenseExpiryDate,
                Status, Languages, Certifications, CertificationsCount)
            VALUES (@PortCode, @PortName, @PilotName, @PilotCode, @PilotType,
                @PilotClass, @CertificationLevel, @ExperienceYears, @MaxVesselGT, @MaxVesselLOA,
                @NightOperations, @AdverseWeather, @CanTrain, @LicenseIssueDate, @LicenseExpiryDate,
                @Status, @Languages, @Certifications, @CertificationsCount);
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.QuerySingleAsync<int>(sql, pilot);
    }

    public async Task<bool> UpdateAsync(Pilot pilot)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE PILOTS SET
                PortCode = @PortCode, PortName = @PortName, PilotName = @PilotName,
                PilotCode = @PilotCode, PilotType = @PilotType, PilotClass = @PilotClass,
                CertificationLevel = @CertificationLevel, ExperienceYears = @ExperienceYears,
                MaxVesselGT = @MaxVesselGT, MaxVesselLOA = @MaxVesselLOA,
                NightOperations = @NightOperations, AdverseWeather = @AdverseWeather,
                CanTrain = @CanTrain, LicenseIssueDate = @LicenseIssueDate,
                LicenseExpiryDate = @LicenseExpiryDate, Status = @Status,
                Languages = @Languages, Certifications = @Certifications,
                CertificationsCount = @CertificationsCount
            WHERE PilotId = @PilotId";
        int rowsAffected = await connection.ExecuteAsync(sql, pilot);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(int pilotId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM PILOTS WHERE PilotId = @PilotId";
        int rowsAffected = await connection.ExecuteAsync(sql, new { PilotId = pilotId });
        return rowsAffected > 0;
    }
}
