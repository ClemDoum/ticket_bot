#!/usr/bin/env python
# coding=utf-8
import logging
import os
import time
import traceback
import ujson
import webbrowser

import requests

from config import get_console_handler, get_data_path, FB_ACCESS_TOKEN

FACEBOOK_GRAPH_URL = "https://graph.facebook.com/"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(get_console_handler())

POST_DATABASE_PATH = os.path.join(get_data_path(), "posts_db.json")
REQUEST_FREQUENCY = 10
EVENT_ID = 166530800395978
TIMEOUT = 5

ERROR_URL = "http://bluegg.co.uk/404"

SELLING_KEYWORDS = ["vend", "à vendre", "en vente"]

TICKETSWAP_KEYWORDS = ["Jeremy Underground le 30 avril 2016",
                       "Jeremy Underground on 30 avril"]

TICKETSWAP_NEGATIVE_KEYWORDS = ["I'm looking", "Je recherche"]


def get_feed_url(event_id):
    return "%s/%s/%s" % (FACEBOOK_GRAPH_URL, EVENT_ID, "feed")


def get_event_feed(event_id):
    try:
        response = requests.request(
            "GET", get_feed_url(event_id), timeout=TIMEOUT,
            params=dict(access_token=FB_ACCESS_TOKEN))
    except requests.HTTPError as e:
        webbrowser.open(ERROR_URL)
        response = ujson.loads(e.read())
        logger.error("FB API error:\n " % str(response))
        raise requests.HTTPError(response)
    except Exception as e:
        webbrowser.open(ERROR_URL)
        logger.error("Error:\n %s" % str(e))
        tb = traceback.format_exc()
        raise ValueError("%s \n\n %s" % (str(e), str(tb)))

    result = response.json(encoding="utf8")
    if result and isinstance(result, dict) and result.get("error"):
        raise ValueError("Got error response %s" % str(result))
    return result


def is_selling_on_ticketswap(post):
    message = post["message"]
    for k in TICKETSWAP_KEYWORDS:
        if k in message:
            for nk in TICKETSWAP_NEGATIVE_KEYWORDS:
                if nk in message:
                    return False
            return True
    return False


def is_selling_on_fb(post):
    message = post["message"]
    for k in SELLING_KEYWORDS:
        if k in message:
            return True
    return False


def open_ticket_page():
    feed = get_event_feed(EVENT_ID)
    last_post_id = feed["data"][0]["id"]

    while True:
        time.sleep(REQUEST_FREQUENCY)
        feed = get_event_feed(EVENT_ID)
        latest_post = feed["data"][0]
        latest_post_id = latest_post["id"]
        if latest_post_id != last_post_id:
            # Ticketswapp
            if is_selling_on_ticketswap(latest_post):
                webbrowser.open(latest_post["link"])
            elif is_selling_on_fb(latest_post):
                webbrowser.open(latest_post["actions"][0]["link"])
            else:
                logger.info("New post but not selling...")
        else:
            logger.debug("No new post found...")


if __name__ == '__main__':
    open_ticket_page()
