"""
Weather Scheduler
Manages hourly weather data updates using APScheduler
Runs as background service integrated with FastAPI
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pyodbc

from config import get_settings
from weather_service import get_weather_service

logger = logging.getLogger(__name__)


class WeatherScheduler:
    """
    Manages scheduled weather updates
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.settings = get_settings()
        self._is_running = False

    async def start(self):
        """Start the scheduler"""
        if self._is_running:
            logger.warning("Weather scheduler already running")
            return

        logger.info("Starting weather scheduler...")

        # Job 1: Hourly weather update (runs at :00 every hour)
        self.scheduler.add_job(
            self._hourly_weather_update,
            trigger=CronTrigger(minute=0),  # Every hour at :00
            id="hourly_weather_update",
            name="Hourly Weather Update",
            replace_existing=True
        )

        # Job 2: Daily cleanup (runs at 2 AM)
        self.scheduler.add_job(
            self._daily_cleanup,
            trigger=CronTrigger(hour=2, minute=0),  # 2:00 AM daily
            id="daily_weather_cleanup",
            name="Daily Weather Cleanup",
            replace_existing=True
        )

        # Job 3: Daily reporting (runs at midnight)
        self.scheduler.add_job(
            self._daily_reporting,
            trigger=CronTrigger(hour=0, minute=0),  # Midnight daily
            id="daily_weather_reporting",
            name="Daily Weather Reporting",
            replace_existing=True
        )

        self.scheduler.start()
        self._is_running = True

        logger.info(
            "Weather scheduler started successfully:\n"
            "  - Hourly updates: Every hour at :00\n"
            "  - Daily cleanup: 2:00 AM\n"
            "  - Daily reports: Midnight"
        )

        # Run initial update
        logger.info("Running initial weather update...")
        await self._hourly_weather_update()

    async def stop(self):
        """Stop the scheduler"""
        if not self._is_running:
            return

        logger.info("Stopping weather scheduler...")
        self.scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("Weather scheduler stopped")

    async def _hourly_weather_update(self):
        """
        Hourly job: Update weather for all active vessels
        """
        job_start = datetime.utcnow()
        logger.info(f"=== Starting scheduled weather update at {job_start.isoformat()} ===")

        try:
            service = await get_weather_service()
            stats = await service.update_all_active_vessels()

            logger.info(
                f"Weather update completed:\n"
                f"  - Vessels processed: {stats['vessels_processed']}\n"
                f"  - API calls made: {stats['api_calls_made']}\n"
                f"  - Cache hits: {stats['cache_hits']}\n"
                f"  - Errors: {stats['errors']}\n"
                f"  - Duration: {stats['duration_seconds']:.2f}s"
            )

            # Check if approaching API limit
            await self._check_api_usage_limits()

        except Exception as e:
            logger.error(f"Hourly weather update failed: {e}", exc_info=True)

    async def _daily_cleanup(self):
        """
        Daily job: Clean up expired weather forecasts
        """
        logger.info("=== Starting daily weather cleanup ===")

        try:
            conn = pyodbc.connect(self.settings.db_connection_string)
            cursor = conn.cursor()

            cursor.execute("EXEC dbo.usp_CleanupExpiredWeatherForecasts")
            conn.commit()

            # Get row counts
            messages = []
            while cursor.nextset():
                for row in cursor.fetchall():
                    messages.append(str(row[0]))

            cursor.close()
            conn.close()

            logger.info(
                f"Daily cleanup completed:\n"
                + "\n".join(f"  - {msg}" for msg in messages)
            )

        except Exception as e:
            logger.error(f"Daily cleanup failed: {e}", exc_info=True)

    async def _daily_reporting(self):
        """
        Daily job: Generate weather usage report
        """
        logger.info("=== Generating daily weather report ===")

        try:
            conn = pyodbc.connect(self.settings.db_connection_string)
            cursor = conn.cursor()

            # Get today's API usage
            sql = """
                SELECT
                    COUNT(*) AS TotalCalls,
                    SUM(CASE WHEN CacheHit = 1 THEN 1 ELSE 0 END) AS CacheHits,
                    SUM(CASE WHEN CacheHit = 0 THEN 1 ELSE 0 END) AS ActualAPICalls,
                    COUNT(DISTINCT CONVERT(DATE, CallTimestamp)) AS DaysCovered
                FROM WEATHER_API_USAGE
                WHERE CallTimestamp >= CAST(GETUTCDATE() AS DATE)
            """

            cursor.execute(sql)
            row = cursor.fetchone()

            total_calls = row[0] if row else 0
            cache_hits = row[1] if row else 0
            actual_api_calls = row[2] if row else 0

            cache_hit_rate = (cache_hits / total_calls * 100) if total_calls > 0 else 0

            # Get forecast statistics
            sql_forecasts = """
                SELECT
                    COUNT(*) AS TotalForecasts,
                    COUNT(DISTINCT VesselId) AS UniqueVessels,
                    COUNT(DISTINCT ScheduleId) AS UniqueSchedules,
                    SUM(CASE WHEN LocationType = 'PORT' THEN 1 ELSE 0 END) AS PortForecasts,
                    SUM(CASE WHEN LocationType = 'WAYPOINT' THEN 1 ELSE 0 END) AS WaypointForecasts,
                    SUM(CASE WHEN AlertLevel = 'CRITICAL' THEN 1 ELSE 0 END) AS CriticalAlerts,
                    SUM(CASE WHEN AlertLevel = 'WARNING' THEN 1 ELSE 0 END) AS WarningAlerts
                FROM WEATHER_FORECAST
                WHERE FetchedAt >= CAST(GETUTCDATE() AS DATE)
            """

            cursor.execute(sql_forecasts)
            forecast_row = cursor.fetchone()

            cursor.close()
            conn.close()

            logger.info(
                f"Daily Weather Report:\n"
                f"  API Usage:\n"
                f"    - Total calls: {total_calls}\n"
                f"    - Cache hits: {cache_hits} ({cache_hit_rate:.1f}%)\n"
                f"    - Actual API calls: {actual_api_calls}\n"
                f"  Forecasts:\n"
                f"    - Total forecasts: {forecast_row[0]}\n"
                f"    - Unique vessels: {forecast_row[1]}\n"
                f"    - Port forecasts: {forecast_row[3]}\n"
                f"    - Waypoint forecasts: {forecast_row[4]}\n"
                f"  Alerts:\n"
                f"    - Critical: {forecast_row[5]}\n"
                f"    - Warning: {forecast_row[6]}"
            )

            # Alert if API usage is high
            if actual_api_calls > 50000:  # 50K calls/day threshold
                logger.warning(
                    f"⚠️  High API usage detected: {actual_api_calls} calls today\n"
                    f"Free tier limit: 33,333 calls/day (1M/month)\n"
                    f"Consider optimizing cache settings or reducing update frequency"
                )

        except Exception as e:
            logger.error(f"Daily reporting failed: {e}", exc_info=True)

    async def _check_api_usage_limits(self):
        """Check if approaching API usage limits"""
        try:
            conn = pyodbc.connect(self.settings.db_connection_string)
            cursor = conn.cursor()

            # Get today's API calls
            sql = """
                SELECT COUNT(*) FROM WEATHER_API_USAGE
                WHERE CallTimestamp >= CAST(GETUTCDATE() AS DATE)
                  AND CacheHit = 0
            """

            cursor.execute(sql)
            today_calls = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            # Alert if over 50% of daily limit (16,666 calls)
            if today_calls > 16666:
                logger.warning(
                    f"⚠️  API usage at {today_calls} calls today "
                    f"({today_calls/33333*100:.1f}% of daily limit)"
                )

        except Exception as e:
            logger.error(f"Failed to check API limits: {e}")

    def get_scheduler_status(self) -> dict:
        """Get scheduler status"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return {
            "is_running": self._is_running,
            "jobs": jobs
        }

    async def trigger_manual_update(self):
        """Manually trigger weather update (for testing/admin)"""
        logger.info("Manual weather update triggered")
        await self._hourly_weather_update()


# Global scheduler instance
_scheduler: WeatherScheduler = None


def get_weather_scheduler() -> WeatherScheduler:
    """Get global scheduler instance"""
    global _scheduler

    if _scheduler is None:
        _scheduler = WeatherScheduler()

    return _scheduler


async def start_weather_scheduler():
    """Start the global scheduler"""
    scheduler = get_weather_scheduler()
    await scheduler.start()


async def stop_weather_scheduler():
    """Stop the global scheduler"""
    scheduler = get_weather_scheduler()
    await scheduler.stop()
