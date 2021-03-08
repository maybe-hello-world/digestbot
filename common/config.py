import logging
import os

import sentry_sdk
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from sentry_sdk.integrations.logging import LoggingIntegration
from common.LoggerFactory import create_logger as _create_logger

# sentry.io SDK
SENTRY_URL = os.getenv("SENTRY_URL", "")
if SENTRY_URL:
    sentry_sdk.utils.MAX_STRING_LENGTH = 8192  # undocumented truncation length
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.WARNING  # Send errors as events
    )
    sentry_sdk.init(dsn=SENTRY_URL, integrations=[sentry_logging])


# InfluxDB
def __init_influx():
    token = os.getenv("INFLUX_TOKEN", "")
    config = os.getenv("INFLUX_CONFIG", "")
    if token and config:
        org, bucket, url = config.split("#")
        client = InfluxDBClient(url=url, token=token)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        return lambda record: write_api.write(bucket, org, record)
    else:
        return lambda *x, **y: True


INFLUX_API_WRITE = __init_influx()

__logger = _create_logger(__name__, logging.WARNING)

__available_log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()
if LOG_LEVEL not in __available_log_levels:
    __logger.warning(
        f"Could not parse log level: f{LOG_LEVEL}, default value 'info' is used."
    )
    LOG_LEVEL = "info"
LOG_LEVEL = __available_log_levels[LOG_LEVEL]
