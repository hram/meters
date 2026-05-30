from datetime import date


def is_weekday(d: date) -> bool:
    return d.weekday() < 5


def target_day(year: int, month: int) -> int:
    for day in range(15, 22):
        if is_weekday(date(year, month, day)):
            return day
    raise ValueError(f"No weekday in window for {year}-{month:02d}")


def is_in_window(year: int, month: int, day: int) -> bool:
    if day < 15 or day > 21:
        return False
    return is_weekday(date(year, month, day))


def should_submit(today: date) -> tuple[bool, str]:
    year, month, day = today.year, today.month, today.day
    target = target_day(year, month)
    if day < target:
        return False, f"до окна подачи (первый день: {target}-е)"
    if not is_in_window(year, month, day):
        return False, "вне окна подачи (15–21, пн–пт)"
    return True, "в окне подачи"
