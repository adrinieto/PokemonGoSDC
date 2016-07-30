import logging
from datetime import datetime

from pgoapi import pgoapi

from config import SERVICE_PROVIDER, USERNAME, PASSWORD


def setup_logging():
    # log settings
    # log format
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
    # log level for http request class
    logging.getLogger("requests").setLevel(logging.WARNING)
    # log level for main pgoapi class
    logging.getLogger("pgoapi").setLevel(logging.INFO)
    # log level for internal pgoapi class
    logging.getLogger("rpc_api").setLevel(logging.INFO)

    logging.getLogger("peewee").setLevel(logging.INFO)


def setup_api(position):
    api = pgoapi.PGoApi()

    api.set_position(*position)

    if not api.login(SERVICE_PROVIDER, USERNAME, PASSWORD):
        return None
    return api


def timestamp_to_strftime(timestamp):
    return datetime.fromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d %H:%M:%S')
