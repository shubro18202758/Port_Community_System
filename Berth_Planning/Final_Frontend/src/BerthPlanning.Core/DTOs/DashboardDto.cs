namespace BerthPlanning.Core.DTOs;

public class DashboardMetricsDto
{
    public int TotalVessels { get; set; }
    public int VesselsScheduled { get; set; }
    public int VesselsApproaching { get; set; }
    public int VesselsBerthed { get; set; }
    public int VesselsDeparted { get; set; }
    public int VesselsInQueue { get; set; }
    public int TotalBerths { get; set; }
    public int AvailableBerths { get; set; }
    public int OccupiedBerths { get; set; }
    public decimal BerthUtilization { get; set; }
    public int ActiveConflicts { get; set; }
    public int TodayArrivals { get; set; }
    public int TodayDepartures { get; set; }
    public decimal AverageWaitingTime { get; set; }
}

public class BerthStatusDto
{
    public int BerthId { get; set; }
    public string BerthName { get; set; } = string.Empty;
    public string BerthCode { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string? CurrentVessel { get; set; }
    public DateTime? VesselETA { get; set; }
    public DateTime? VesselETD { get; set; }
    public int NumberOfCranes { get; set; }
    public string? BerthType { get; set; }
}

public class VesselQueueDto
{
    public int VesselId { get; set; }
    public int ScheduleId { get; set; }
    public string VesselName { get; set; } = string.Empty;
    public string? VesselType { get; set; }
    public DateTime? ETA { get; set; }
    public DateTime? PredictedETA { get; set; }
    public string Status { get; set; } = string.Empty;
    public int Priority { get; set; }
    public string? AssignedBerth { get; set; }
    public decimal? LOA { get; set; }
    public decimal? Draft { get; set; }
}

public class TimelineEventDto
{
    public int ScheduleId { get; set; }
    public int BerthId { get; set; }
    public string BerthName { get; set; } = string.Empty;
    public int VesselId { get; set; }
    public string VesselName { get; set; } = string.Empty;
    public DateTime StartTime { get; set; }
    public DateTime EndTime { get; set; }
    public string Status { get; set; } = string.Empty;
    public string? VesselType { get; set; }
}
