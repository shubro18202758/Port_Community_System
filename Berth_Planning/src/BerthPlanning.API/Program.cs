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
builder.Services.AddOpenApi();

// Configure CORS for frontend
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        _ = policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
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

// AIS Integration - Demo mode uses simulated data from database
// For production, register AISStream.io service:
// builder.Services.AddSingleton<IAISStreamService, AISStreamService>();

WebApplication app = builder.Build();

// Enable OpenAPI and Scalar UI
app.MapOpenApi();
app.MapScalarApiReference();

app.UseCors("AllowAll");
app.UseAuthorization();
app.MapControllers();

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

// API info endpoint
app.MapGet("/", () => new
{
    Name = "Berth Planning API",
    Version = "2.0",
    Description = "AI-Powered Berth Planning and Allocation Optimization System with Predictive Analytics",
    Documentation = "/scalar/v1",
    Features = new[]
    {
        "Predictive ETA Calculation",
        "Arrival Deviation Detection",
        "What-If Simulation",
        "Real-Time Re-Optimization",
        "Resource Optimization",
        "Historical Analytics"
    },
    Endpoints = new[]
    {
        "GET /health - Health check",
        "GET /health/db - Database connection test",
        "GET /vessels - List all vessels",
        "GET /berths - List all berths",
        "GET /schedules - List all schedules",
        "GET /dashboard/metrics - Dashboard metrics",
        "GET /suggestions/berth/{vesselId} - AI berth suggestions",
        "GET /predictions/eta/{vesselId} - Predictive ETA calculation",
        "GET /predictions/deviations - Deviation detection",
        "GET /whatif/vessel-delay - What-if simulation",
        "POST /optimization/trigger - Schedule re-optimization",
        "GET /resources/availability - Resource availability",
        "GET /analytics/historical - Historical analytics",
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
