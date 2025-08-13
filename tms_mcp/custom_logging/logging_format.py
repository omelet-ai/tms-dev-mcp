from datetime import datetime, timezone

from pythonjsonlogger.json import JsonFormatter


class CustomFormatter(JsonFormatter):
    def formatTime(self, record, datefmt=None):
        """
        This is a custom formatter for logging that converts datetime to use nation-specific time zone
        """
        dt = datetime.fromtimestamp(record.created, timezone.utc)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            try:
                s = dt.isoformat(timespec="milliseconds")
            except TypeError:
                s = dt.isoformat()
        return s


# Configure logging
formatter = CustomFormatter(
    fmt="{asctime} - {name} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S %Z%z",
)
