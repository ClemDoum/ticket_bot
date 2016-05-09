import logging
import os
import sys

from colorlog import ColoredFormatter

FB_ACCESS_TOKEN = "your_fb_access_token"


def get_root_path():
    return os.path.dirname(os.path.abspath(__file__))


def get_data_path():
    return os.path.join(get_root_path(), "data")


def get_test_data_path():
    return os.path.join(get_root_path(), "tests", "data")


# Logging
LOG_FORMATTER = ColoredFormatter(
    '%(log_color)s[%(levelname)s][%(asctime)s][%(name)s]: '
    '%(reset)s%(message)s',
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)


def get_console_handler():
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(LOG_FORMATTER)
    return ch
