"""Example beat schedules for _example extension.

Beat schedules define when periodic tasks should run. Celery Beat reads these
schedules and triggers tasks at the specified times.

## Usage

1. Create `tasks/schedules.py` in your extension directory
2. Define a `SCHEDULES` dictionary with crontab expressions
3. Enable your extension in `.env`: `ENABLED_EXTENSIONS=your_extension`
4. Start beat scheduler: `make beat` (local) or `make infra-up` (Docker)
5. Schedules are auto-discovered at startup and prefixed with extension name

## Schedule Key Format

Schedule keys are automatically prefixed with extension name to prevent conflicts:
- Your key: `"daily-cleanup"`
- Registered as: `"your_extension.daily-cleanup"`

## Crontab Expressions

Common patterns:
- `crontab()` - Every minute
- `crontab(minute=0, hour=0)` - Midnight daily
- `crontab(minute="*/15")` - Every 15 minutes
- `crontab(hour="*/3")` - Every 3 hours
- `crontab(day_of_week="mon")` - Every Monday
- `crontab(day_of_month="1")` - First day of month

Timezone: Schedules execute in the timezone set in `CELERY_TIMEZONE` (.env)

## Task Reference

Use dynamic task names via settings for consistency:
- `f"{settings.CELERY_TASKS_MODULE}.task_name"`
- Resolves to: `"app.tasks.task_name"`

## Example Schedules

Below are example schedules demonstrating different patterns. Uncomment and
modify for your use case.
"""

# Example schedules (commented out - modify for your use case)
SCHEDULES = {
    # # Daily task at midnight
    # "example-daily-task": {
    #     "task": f"{settings.CELERY_TASKS_MODULE}.example_task",
    #     "schedule": crontab(hour=0, minute=0),  # Midnight in CELERY_TIMEZONE
    #     "args": (),
    #     "kwargs": {},
    # },
    # # Frequent task every 15 minutes
    # "example-frequent-task": {
    #     "task": f"{settings.CELERY_TASKS_MODULE}.another_example_task",
    #     "schedule": crontab(minute="*/15"),
    #     "args": ("arg1", "arg2"),
    # },
    # # Weekly task every Monday at 9 AM
    # "example-weekly-task": {
    #     "task": f"{settings.CELERY_TASKS_MODULE}.weekly_cleanup",
    #     "schedule": crontab(hour=9, minute=0, day_of_week="mon"),
    #     "args": (),
    # },
    # # Hourly task at minute 30 (:30 past every hour)
    # "example-hourly-task": {
    #     "task": f"{settings.CELERY_TASKS_MODULE}.hourly_sync",
    #     "schedule": crontab(minute=30),
    #     "args": (),
    # },
}
