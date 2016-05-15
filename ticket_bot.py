#!/usr/bin/env python
# coding=utf-8
import argparse
import logging
import time
import traceback
import webbrowser
from abc import ABCMeta, abstractmethod
from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP
from urlparse import parse_qs

import requests

from config import (get_console_handler, FB_APP_ID, FB_APP_SECRET,
                    WEBBROWSER_ERROR_URL, EMAIL_SENDER, SMTP_HOST, SMTP_USER,
                    SMTP_PASSWORD)

FACEBOOK_GRAPH_URL = "https://graph.facebook.com/"
FACEBOOK_OAUTH_DIALOG_URL = "https://www.facebook.com/dialog/oauth?"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(get_console_handler())

SELLING_KEYWORDS = ["vend", "à vendre", "en vente", "j'ai"]
TICKETSWAP_NEGATIVE_KEYWORDS = ["I'm looking", "Je recherche"]
VALID_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6"]


class TicketBot:
    __metaclass__ = ABCMeta

    def __init__(self, event_id, ticketswap_keywords, api_version="2.6",
                 request_frequency=18, timeout=10):

        self.event_id = event_id
        self.event_feed_path = "%s/%s" % (event_id, "feed")

        if str(api_version) not in VALID_API_VERSIONS:
            raise ValueError("Valid API versions are " +
                             str(VALID_API_VERSIONS).strip("[]"))
        self.api_version = api_version
        self.ticketswap_keywords = ticketswap_keywords
        self.request_frequency = request_frequency
        self.last_post = None
        self.timeout = timeout
        self.access_token = None

    def request(self, method, path, params=None):
        params = params or dict()
        response = None
        if self.access_token:
            params["access_token"] = self.access_token["access_token"]
        try:
            response = requests.request(method,
                                        FACEBOOK_GRAPH_URL + path,
                                        timeout=self.timeout,
                                        params=params)
        except Exception as e:
            self.handle_error(e)

        headers = response.headers
        if "json" in headers["content-type"]:
            result = response.json(encoding="utf8")
        elif "access_token" in parse_qs(response.text):
            query_str = parse_qs(response.text)
            result = {"access_token": query_str["access_token"][0]}
            if "expires" in query_str:
                result["expires"] = query_str["expires"][0]
        else:
            raise ValueError("Invalid response: %s" % str(response))

        if result and isinstance(result, dict) and result.get("error"):
            raise ValueError("Got error response %s" % str(result))

        return result

    def set_access_token(self, ):
        params = {"grant_type": "client_credentials",
                  "client_id": FB_APP_ID,
                  "client_secret": FB_APP_SECRET}
        self.access_token = self.request("GET", "oauth/access_token",
                                         params=params)
        logger.info("Successfully set access token")

    def renew_access_token(self, ):
        params = {
            "client_id":
                FB_APP_ID,
            "client_secret": FB_APP_SECRET,
            "grant_type": "fb_exchange_token",
            "fb_exchange_token": self.access_token,
        }

        self.access_token = self.request("GET", "oauth/access_token",
                                         params=params)
        logger.info("Successfully renewed access token")

    def get_event_feed(self):
        result = self.request("GET", self.event_feed_path)
        return result

    def get_event_posts(self):
        feed = self.get_event_feed()
        return feed["data"]

    def get_event_latest_post(self):
        posts = self.get_event_posts()
        if len(posts) > 0:
            return posts[0]
        else:
            return None

    def get_link(self, post, source):
        params = dict(fields="actions,link")

        if source == "ticketswap":
            link = post["link"]
        elif source == "private_message":
            link = post["actions"][0]["link"]
        else:
            raise ValueError("Unvalid source. Expected %s fround %s"
                             % (
                                 str(["ticketswap", "private_message"]),
                                 source))
        return link

    def run(self):
        try:
            logger.debug("Getting access token...")
            self.set_access_token()
            self.last_post = self.get_event_latest_post()
            while True:
                time.sleep(self.request_frequency)
                latest_post = self.get_event_latest_post()
                if self.last_post["id"] != latest_post["id"]:
                    logger.debug("Found new post, identifying source post...")
                    self.last_post = latest_post
                    source = self.get_selling_source(latest_post)
                    if source is not None:
                        logger.debug("Ticket coming form %s" % str(source))
                        self.notify(latest_post, source)
                    else:
                        logger.debug("Did not find any selling source in post")
                else:
                    logger.debug("No new post found...")
        except Exception, e:
            self.handle_error(e)

    def get_selling_source(self, post):
        message = post["message"]
        # Private message
        for k in SELLING_KEYWORDS:
            if k in message:
                return "private_message"
        # Ticketswap
        for k in self.ticketswap_keywords:
            if k in message:
                for nk in TICKETSWAP_NEGATIVE_KEYWORDS:
                    if nk in message:
                        return False
                return "ticketswap"
        return False

    @abstractmethod
    def notify(self, post, source):
        pass

    @abstractmethod
    def handle_error(self, e):
        pass


class EmailTicketBot(TicketBot):
    def __init__(self, event_id, ticketswap_keywords, api_version="2.6",
                 request_frequency=18, timeout=10, receivers=list()):
        super(EmailTicketBot, self).__init__(
            event_id=event_id, ticketswap_keywords=ticketswap_keywords,
            api_version=api_version, request_frequency=request_frequency,
            timeout=timeout)
        self.receivers = receivers

    def notify(self, post, source):
        link = self.get_link(post, source)
        msg = MIMEText("Ticket available here: %s" % link)
        msg["From"] = EMAIL_SENDER
        msg["Subject"] = "Your TicketBot found you tickets"
        s = SMTP(SMTP_HOST)
        s.login(SMTP_USER, SMTP_PASSWORD)
        try:
            s.sendmail(EMAIL_SENDER, self.receivers, msg.as_string())
        finally:
            s.quit()

    def handle_error(self, e):
        tb = traceback.format_exc()
        subject = "TicketBot error"
        content = "TicketBot error: %s \n\n Traceback: %s" % (e, tb)
        self.send_email(subject, content)
        tb = traceback.format_exc()
        logger.error("Error:\n %s \n\n Traceback:\n%s" % (str(e), tb))
        raise

    def send_email(self, subject, content):
        msg = MIMEText(content)
        msg["From"] = EMAIL_SENDER
        msg["Subject"] = subject
        s = SMTP(SMTP_HOST)
        s.login(SMTP_USER, SMTP_PASSWORD)
        try:
            s.sendmail(EMAIL_SENDER, self.receivers, msg.as_string())
        finally:
            s.quit()


class BrowserTicketBot(TicketBot):
    def notify(self, post, source):
        link = self.get_link(post, source)
        webbrowser.open(link)

    def handle_error(self, e):
        webbrowser.open(WEBBROWSER_ERROR_URL)
        tb = traceback.format_exc()
        logger.error("Error:\n %s \n\n Traceback:\n%s" % (str(e), tb))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot that grabs ticket from "
                                                 "FB event page...")
    parser.add_argument("event_id", type=str, help="FB event ID")
    parser.add_argument("ticketswap_keywords", type=str, nargs="+",
                        help="Title of the ticketswap event (is used to "
                             "identify ticketswap posts)")
    parser.add_argument("--api-version", type=str, default="2.6",
                        help="FB Graph API version")
    parser.add_argument("--request-frequency", type=int, default=5 * 60,
                        help="Update frequency of the bot")

    args = parser.parse_args()
    bot = BrowserTicketBot(**vars(args))
    bot.run()
