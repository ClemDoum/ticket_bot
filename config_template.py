import logging
import os
import sys

from colorlog import ColoredFormatter

# Facebook
FB_APP_SECRET = "your_fb_app_secret"
FB_APP_ID = "your_fb_app_id"

# Email notifications settings
EMAIL_SENDER = "sender_email_address"
SMTP_HOST = "your_smtp_host_server"
SMTP_USER = "your_smtp_user"
SMTP_PASSWORD = "your_smtp_password"


WEBBROWSER_ERROR_URL = "http://bluegg.co.uk/404"

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
