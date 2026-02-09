using BerthPlanning.API.Hubs;
using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using BerthPlanning.Infrastructure.Repositories;
using BerthPlanning.Infrastructure.Services;
using Scalar.AspNetCore;
using System.Data;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddSignalR();

// Configure CORS for frontend (SignalR requires credentials)
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        _ = policy.WithOrigins("http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173")
              .AllowAnyMethod()
              .AllowAnyHeader()
              .AllowCredentials();
    });
});

// Database connection
string connectionString = builder.Configuration.GetConnectionString("DefaultConnection")
    ?? "Server=localhost;Database=BerthPlanning;Trusted_Connection=True;TrustServerCertificate=True;";

builder.Services.AddSingleton<IDbConnectionFactory>(sp => new DbConnectionFactory(connectionString));

// Register repositories
builder.Services.AddScoped<IVesselRepository, VesselRepository>();
builder.Services.AddScoped<IBerthRepository, BerthRepository>();
builder.Services.AddScoped<IScheduleRepository, ScheduleRepository>();
builder.Services.AddScoped<IDashboardRepository, DashboardRepository>();
builder.Services.AddScoped<IPortRepository, PortRepository>();
builder.Services.AddScoped<ITerminalRepository, TerminalRepository>();
builder.Services.AddScoped<IResourceRepository, ResourceRepository>();
builder.Services.AddScoped<IChannelRepository, ChannelRepository>();
builder.Services.AddScoped<IAnchorageRepository, AnchorageRepository>();
builder.Services.AddScoped<IPilotRepository, PilotRepository>();
builder.Services.AddScoped<ITugboatRepository, TugboatRepository>();

// Register services
builder.Services.AddScoped<IConstraintValidator, ConstraintValidator>();
builder.Services.AddScoped<IScoringEngine, ScoringEngine>();
builder.Services.AddScoped<ISuggestionService, SuggestionService>();

// Register Phase 1 & 2 services - AI-Powered Features
builder.Services.AddScoped<IPredictionService, PredictionService>();
builder.Services.AddScoped<IWhatIfService, WhatIfService>();
builder.Services.AddScoped<IReoptimizationService, ReoptimizationService>();
builder.Services.AddScoped<IResourceOptimizationService, ResourceOptimizationService>();
builder.Services.AddScoped<IAnalyticsService, AnalyticsService>();

// Register Google OR-Tools Optimization Service
builder.Services.AddScoped<IBerthOptimizationOrToolsService, BerthOptimizationOrToolsService>();

// Register AI Service Client - connects to Python AI backend
builder.Services.AddHttpClient<IAIServiceClient, AIServiceClient>(client =>
{
    client.BaseAddress = new Uri(builder.Configuration["AIService:BaseUrl"] ?? "http://localhost:8000");
    client.Timeout = TimeSpan.FromSeconds(
        int.TryParse(builder.Configuration["AIService:TimeoutSeconds"], out var timeout) ? timeout : 60
    );
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

WebApplication app = builder.Build();

// Enable OpenAPI and Scalar UI
app.UseSwagger();
app.UseSwaggerUI();
app.MapScalarApiReference();

app.UseCors("AllowAll");
app.UseAuthorization();
app.MapControllers();
app.MapHub<VesselTrackingHub>("/hubs/vesseltracking");

// Health check endpoint (no database required)
app.MapGet("/health", () => new
{
    Status = "Healthy",
    Timestamp = DateTime.UtcNow,
    Environment = app.Environment.EnvironmentName
});

// Database connection test endpoint
app.MapGet("/health/db", async (IDbConnectionFactory dbFactory) =>
{
    try
    {
        using IDbConnection connection = dbFactory.CreateConnection();
        connection.Open();
        return Results.Ok(new { Status = "Database Connected", Timestamp = DateTime.UtcNow });
    }
    catch (Exception ex)
    {
        return Results.Json(new { Status = "Database Error", Error = ex.Message }, statusCode: 500);
    }
});

// AI Service health check endpoint
app.MapGet("/health/ai", async (IAIServiceClient aiService) =>
{
    try
    {
        var health = await aiService.GetHealthAsync();
        return Results.Ok(new
        {
            Status = health.Status == "healthy" ? "AI Service Connected" : "AI Service Degraded",
            AIStatus = health,
            Timestamp = DateTime.UtcNow
        });
    }
    catch (Exception ex)
    {
        return Results.Json(new { Status = "AI Service Unreachable", Error = ex.Message }, statusCode: 503);
    }
});

// API info endpoint
app.MapGet("/", () => new
{
    Name = "Berth Planning API",
    Version = "3.0",
    Description = "AI-Powered Berth Planning and Allocation Optimization System with Full Training Data",
    Documentation = "/scalar/v1",
    Features = new[]
    {
        "Google OR-Tools CP-SAT Global Optimization",
        "Predictive ETA Calculation",
        "Arrival Deviation Detection",
        "What-If Simulation",
        "Real-Time Re-Optimization",
        "Resource Optimization",
        "Historical Analytics",
        "Channel & Anchorage Management",
        "Pilot & Tugboat Fleet Management",
        "150 Ports, 2848 Berths, 3000 Vessels Training Data",
        "Claude AI-Powered Agents (ETA, Berth, Conflict)",
        "RAG Knowledge Base Integration",
        "AI Chatbot with NLU",
        "Multi-Agent Orchestration"
    },
    Endpoints = new[]
    {
        "GET /health - Health check",
        "GET /health/db - Database connection test",
        "GET /health/ai - AI service health check",
        "GET /vessels - List all vessels",
        "GET /berths - List all berths",
        "GET /schedules - List all schedules",
        "GET /dashboard/metrics - Dashboard metrics",
        "GET /suggestions/berth/{vesselId} - AI berth suggestions",
        "GET /predictions/eta/{vesselId} - Predictive ETA calculation",
        "GET /predictions/deviations - Deviation detection",
        "GET /whatif/vessel-delay - What-if simulation",
        "POST /optimization/trigger - Schedule re-optimization",
        "POST /optimization/ortools/global - OR-Tools global schedule optimization",
        "GET /optimization/ortools/vessel/{vesselId} - OR-Tools single vessel optimization",
        "GET /optimization/ortools/feasibility - Check schedule feasibility",
        "GET /resources - List all resources",
        "POST /ai/chat - AI Chatbot",
        "POST /ai/explain - RAG Explanation",
        "GET /ai/eta/{vesselId} - Claude ETA Prediction",
        "GET /ai/berth/{vesselId} - Claude Berth Optimization",
        "GET /ai/conflicts - Claude Conflict Detection",
        "POST /ai/process-arrival/{vesselId} - Multi-Agent Processing",
        "POST /ai/whatif - AI What-If Simulation",
        "GET /scalar/v1 - API documentation (Scalar UI)"
    }
});

Console.WriteLine("===========================================");
Console.WriteLine("  Berth Planning API Started");
Console.WriteLine("===========================================");
Console.WriteLine($"  Scalar UI: http://localhost:5185/scalar/v1");
Console.WriteLine($"  OpenAPI JSON: http://localhost:5185/openapi/v1.json");
Console.WriteLine($"  Health Check: http://localhost:5185/health");
Console.WriteLine($"  API Info: http://localhost:5185/");
Console.WriteLine("===========================================");

app.Run();
