namespace BerthPlanning.Core.DTOs;

public class CreateScheduleDto
{
    public int VesselId { get; set; }
    public int? BerthId { get; set; }
    public DateTime? ETA { get; set; }
    public DateTime? ETD { get; set; }
    public int? DwellTime { get; set; }
}

public class UpdateScheduleDto
{
    public int? VesselId { get; set; }
    public int? BerthId { get; set; }
    public DateTime? ETA { get; set; }
    public DateTime? PredictedETA { get; set; }
    public DateTime? ETD { get; set; }
    public DateTime? ATA { get; set; }
    public DateTime? ATB { get; set; }
    public DateTime? ATD { get; set; }
    public string? Status { get; set; }
    public int? DwellTime { get; set; }
    public int? WaitingTime { get; set; }
}

public class UpdateETADto
{
    public DateTime NewETA { get; set; }
    public DateTime? NewPredictedETA { get; set; }
}

public class RecordArrivalDto
{
    public DateTime ATA { get; set; }
}

public class RecordBerthingDto
{
    public DateTime ATB { get; set; }
}

public class RecordDepartureDto
{
    public DateTime ATD { get; set; }
}

public class AllocateBerthDto
{
    public int VesselId { get; set; }
    public int BerthId { get; set; }
    public DateTime ETA { get; set; }
    public DateTime ETD { get; set; }
    public int? DwellTime { get; set; }
}

public class AllocationResultDto
{
    public bool Success { get; set; }
    public int? ScheduleId { get; set; }
    public string Message { get; set; } = string.Empty;
    public List<string> Warnings { get; set; } = [];
    public List<ConflictDto> Conflicts { get; set; } = [];
}

public class ConflictDto
{
    public int ConflictId { get; set; }
    public string ConflictType { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public int Severity { get; set; }
    public string Status { get; set; } = string.Empty;
}
