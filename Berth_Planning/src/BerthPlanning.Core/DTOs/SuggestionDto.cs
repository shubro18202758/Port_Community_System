namespace BerthPlanning.Core.DTOs;

public class BerthSuggestionRequestDto
{
    public int VesselId { get; set; }
    public DateTime? PreferredETA { get; set; }
}

public class BerthSuggestionDto
{
    public int Rank { get; set; }
    public int BerthId { get; set; }
    public string BerthName { get; set; } = string.Empty;
    public string BerthCode { get; set; } = string.Empty;
    public decimal Score { get; set; }
    public string Confidence { get; set; } = "MEDIUM";
    public DateTime ProposedETA { get; set; }
    public DateTime ProposedETD { get; set; }
    public int EstimatedWaitMinutes { get; set; }
    public List<string> Reasoning { get; set; } = [];
    public ConstraintCheckDto Constraints { get; set; } = new();
}

public class ConstraintCheckDto
{
    public int HardConstraintsMet { get; set; }
    public int HardConstraintsTotal { get; set; }
    public decimal SoftConstraintScore { get; set; }
    public List<ConstraintViolationDto> Violations { get; set; } = [];
}

public class ConstraintViolationDto
{
    public string ConstraintId { get; set; } = string.Empty;
    public string ConstraintName { get; set; } = string.Empty;
    public string Severity { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
}

public class SuggestionResponseDto
{
    public int VesselId { get; set; }
    public string VesselName { get; set; } = string.Empty;
    public DateTime RequestedAt { get; set; }
    public List<BerthSuggestionDto> Suggestions { get; set; } = [];
    public string? Message { get; set; }
}

public class ConflictResolutionOptionDto
{
    public string Option { get; set; } = string.Empty;
    public string Action { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public int ImpactScore { get; set; }
    public string Reasoning { get; set; } = string.Empty;
}

public class ConflictResolutionDto
{
    public int ConflictId { get; set; }
    public string ConflictType { get; set; } = string.Empty;
    public List<int> AffectedVessels { get; set; } = [];
    public List<ConflictResolutionOptionDto> Options { get; set; } = [];
    public string AIRecommendation { get; set; } = string.Empty;
    public string Confidence { get; set; } = "MEDIUM";
}
