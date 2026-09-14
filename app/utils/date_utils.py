import calendar
from datetime import date


def get_next_due_date(
    current_due_date: date,
    original_rent_day: int
) -> date:

    # Move to the next month
    if current_due_date.month == 12:
        next_year = current_due_date.year + 1
        next_month = 1
    else:
        next_year = current_due_date.year
        next_month = current_due_date.month + 1

    # Get the last valid day of the next month
    last_day = calendar.monthrange(
        next_year,
        next_month
    )[1]

    # Use the original rent day if it exists.
    # Otherwise use the last day of the month.
    next_day = min(
        original_rent_day,
        last_day
    )

    return date(
        next_year,
        next_month,
        next_day
    )