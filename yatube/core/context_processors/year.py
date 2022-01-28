from datetime import datetime


def year(request) -> int:
    """Добавляет переменную с текущим годом."""
    current_year = datetime.now().year
    return {
        "year": int(current_year),
    }
