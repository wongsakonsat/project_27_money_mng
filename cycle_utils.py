"""
Cycle Utility Module
Handles custom financial cycle math (23rd of current month to 22nd of next month)
and dynamic burn rate calculations.
"""

from datetime import date, datetime, timedelta
import calendar
import config

def add_months(sourcedate: date, months: int) -> date:
    """Add or subtract months safely preserving day boundaries."""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def get_cycle_for_date(target_date: date | str) -> tuple[str, date, date, str]:
    """
    Returns (cycle_id, start_date, end_date, display_label) for any given date.
    Cycle starts on the 23rd of month M and ends on the 22nd of month M+1.
    """
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    
    if target_date.day >= config.CYCLE_START_DAY:
        start_date = date(target_date.year, target_date.month, config.CYCLE_START_DAY)
        # End date is 22nd of next month
        next_month_date = add_months(start_date, 1)
        end_date = date(next_month_date.year, next_month_date.month, config.CYCLE_END_DAY)
    else:
        # Before 23rd, so cycle started on 23rd of previous month
        prev_month_date = add_months(target_date, -1)
        start_date = date(prev_month_date.year, prev_month_date.month, config.CYCLE_START_DAY)
        end_date = date(target_date.year, target_date.month, config.CYCLE_END_DAY)
        
    cycle_id = f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
    # Friendly Thai / English label: e.g. "รอบ 23 ก.ค. - 22 ส.ค. 2026"
    thai_months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    start_m_th = thai_months[start_date.month - 1]
    end_m_th = thai_months[end_date.month - 1]
    display_label = f"รอบ {start_date.day} {start_m_th} - {end_date.day} {end_m_th} {end_date.year} ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')})"
    
    return cycle_id, start_date, end_date, display_label

def get_current_cycle_info(as_of_date: date | None = None) -> dict:
    """
    Computes comprehensive stats for the active cycle relative to as_of_date.
    """
    if as_of_date is None:
        as_of_date = date.today()
        
    cycle_id, start_date, end_date, display_label = get_cycle_for_date(as_of_date)
    
    total_days = (end_date - start_date).days + 1
    days_elapsed = (as_of_date - start_date).days + 1
    days_remaining = (end_date - as_of_date).days # Remaining days from tomorrow or today
    days_left_inclusive = max(1, (end_date - as_of_date).days + 1)
    
    progress_pct = min(100.0, max(0.0, (days_elapsed / total_days) * 100))
    
    return {
        "cycle_id": cycle_id,
        "start_date": start_date,
        "end_date": end_date,
        "display_label": display_label,
        "as_of_date": as_of_date,
        "total_days": total_days,
        "days_elapsed": max(1, min(days_elapsed, total_days)),
        "days_remaining": max(0, days_remaining),
        "days_left_inclusive": days_left_inclusive,
        "progress_pct": progress_pct
    }

def calculate_food_burn_metrics(spent_food: float, cycle_info: dict, base_daily_budget: float = 350.0) -> dict:
    """
    Computes live dynamic burn rate for daily food.
    Monthly Food Target = base_daily_budget * total_days (approx 10,500 THB)
    """
    total_days = cycle_info["total_days"]
    days_elapsed = cycle_info["days_elapsed"]
    days_left = cycle_info["days_left_inclusive"]
    
    total_budget = base_daily_budget * total_days
    remaining_budget = total_budget - spent_food
    
    # Actual daily spend rate so far
    actual_burn_rate = spent_food / days_elapsed if days_elapsed > 0 else 0.0
    
    # Dynamic allowance remaining per day for the rest of the cycle
    if days_left > 0:
        dynamic_daily_allowance = max(0.0, remaining_budget / days_left)
    else:
        dynamic_daily_allowance = 0.0
        
    # Expected spend by today under ideal linear pacing
    ideal_spend_to_date = base_daily_budget * days_elapsed
    pace_diff = spent_food - ideal_spend_to_date # Positive means over-burning, negative means saving
    
    if pace_diff > 350:
        status_color = "#EF4444" # Red - Over budget
        status_text = "⚠️ เผาเงินเร็วกว่าแผน (Over Pace)"
    elif pace_diff < -350:
        status_color = "#10B981" # Green - Saving well
        status_text = "✨ คุมงบได้ดีมาก (Under Budget)"
    else:
        status_color = "#3B82F6" # Blue - On track
        status_text = "🎯 เป็นไปตามเป้าหมาย (On Track)"
        
    return {
        "total_food_budget": total_budget,
        "spent_food": spent_food,
        "remaining_budget": remaining_budget,
        "spent_pct": min(100.0, (spent_food / total_budget * 100)) if total_budget > 0 else 0,
        "actual_burn_rate": actual_burn_rate,
        "dynamic_daily_allowance": dynamic_daily_allowance,
        "base_daily_budget": base_daily_budget,
        "pace_diff": pace_diff,
        "status_color": status_color,
        "status_text": status_text
    }
