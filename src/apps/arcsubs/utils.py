from datetime import datetime

import pytz


TIMEZONE = pytz.timezone('America/Lima')


def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(
        timestamp / 1000,
        tz=TIMEZONE
    )


def start_today_date():
    starts = datetime.combine(
        datetime.today(),
        datetime.min.time()
    )
    return TIMEZONE.localize(starts)


def date_to_localtime(date_to_format):
    try:
        return date_to_format.astimezone(TIMEZONE)
    except Exception as e:
        return ''
