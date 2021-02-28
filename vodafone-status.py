#!/usr/bin/env python

# Pages in 2021 are more dynamic than 1990.  So the state of the page is not so
# deterministic.   Heuristics for waiting unitl data is mature are required.
#
# Docs at pypi.org/project/selenium gives an example using googletest
# Tips : see e.g.
# browserstack.com/guide/python-selenium-to-run-web-automation-test

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import json
import time
import os
import pdb
import logging
import inotify.adapters
import re
import requests
import shutil
import sys
#import threading

COLLATE_IN="/home/astephen/git-wd/vodafone-router-status"

_DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

_LOGGER = logging.getLogger(__name__)

from vfstats import SystemStats, DslStats

class VodafoneMonitor:


    ip = "192.168.1.1"
    hostname = "vodafone.broadband"
    # chromedriver is a required executable per version of chrome
    # and must be in the PATH 
    chromedriver = 'chromedriver'

    def __init__(self, with_chrome = False):
        self.t0 = time.time()
        self.driver = None
        if with_chrome:
            self.init_driver()
        self.sessionID = None

    def init_driver(self):
        options = Options()
        #options.add_argument("--headless")
        self.driver = webdriver.Chrome(self.chromedriver, options = options)
        # Give the app time to start up (horrible race conditions)
        time.sleep(2)
        self.driver.fullscreen_window()


    def fs(self):
        """Keep forcing window back to fullscreen"""
        self.driver.fullscreen_window()


    def full_url(self, suffix, byhost = True):
        addr = self.hostname if byhost else self.ip
        return "http://{}/{}".format(addr, suffix)

    def authenticate(self, pwd):
        """With no wait - the timeout is uncontrolled. Exception will occur
        unless we loop."""
        t0 = time.time()
        self.driver.get('http://vodafone.broadband/login.lp')
        # TODO: screenscrape the WAN address here
        password = self.driver.find_element_by_id("login-txt-pwd")
        password.send_keys(pwd)
        self.driver.find_element_by_id("login-btn-logIn").click()
        try:
            logged_in = self.driver.find_element_by_id("home-str-numofusr")
        except:
            _LOGGER.info("Impatient : need the next page before we can get the next element")
        #pdb.set_trace()

        _LOGGER.info("authenticate completed in {}".format(time.time() - t0))

    def find_by_id(self, element_name, timeout = 10, explicit = True):
        if timeout is None: 
            return self.driver.find_element_by_id(element_name)
        else:
            if explicit:
                try:
                    element = WebDriverWait(self.driver, timeout).until(
                            EC.presence_of_element_located((By.ID, element_name))
                            )
                except:
                    raise ValueError("Timed out waiting for {}".format(element_name))
                else:
                    _LOGGER.info("Found {}".format(element_name))
                    return element

    def authenticate_wait_explicit(self, pwd, timeout):
        """Explicit wait will wait up to timeout but return earlier if action
        completes."""
        t0 = time.time()
        self.driver.get('http://vodafone.broadband/login.lp')
        password = self.find_by_id("login-txt-pwd", 10)
        password.send_keys(pwd)
        self.driver.find_element_by_id("login-btn-logIn").click()
        self.find_by_id("home-str-numofusr", 10)
        t1 = time.time()
        _LOGGER.info("authenticate_wait_explicit {} completed by {} in {}".format(timeout, t1 - self.t0, t1 - t0))
        self.fs()
        self.cookies_list = self.driver.get_cookies() 
        self.cookies_json = list(json.dumps(self.cookies_list))
        #pdb.set_trace()
        for c in self.cookies_list:
            if c['name'] == 'sessionID':
                self.sessionID = c['value']

    def authenticate_wait_implicit(self, pwd, timeout):
        """Implicit wait will wait the full duration and then try to carry
        on."""
        t0 = time.time()
        self.driver.get('http://vodafone.broadband/login.lp')
        password = self.driver.find_element_by_id("login-txt-pwd")
        password.send_keys(pwd)
        _LOGGER.info("authenticate_wait_implicit {} completed in {}".format(timeout, time.time() - t0))

    def modals_request(self):
        if self.sessionID is not None:
            # The infor in theese Info classes is equivalent
            info_map = {
                    "status=systemInfo" : "systemInfo",
                    "status=wifiInfo" : "wifiInfo",
                    "status=networkInfo" : "networkInfo",
                    "status=arp" : "arp"
                    }
            info_map = {
                    "status=systemInfo" : "systemInfo",
                    "status=arp" : "arp"
                    }
            base_url="http://vodafone.broadband/modals/status-support/status.lp?{}"
            for (uarg, ulabel) in info_map.items():
                url = base_url.format(uarg)
                cookies = {'sessionID' : self.sessionID}
                r = requests.get(url, cookies = cookies)
                text = r.text
                stat = r.status_code
                system_stats = SystemStats(ulabel,text) 
                csv_path = os.path.join(COLLATE_IN, "system_stats.csv")
                if ulabel == "systemInfo":
                    with open(csv_path, "a") as fh:
                        fh.write("{}\n".format(system_stats.as_csv()))
            dsl_base_url="http://vodafone.broadband/modals/status-support/vdslStatus.lp"
            cookies = {'sessionID' : self.sessionID}
            r = requests.get(dsl_base_url, cookies = cookies)
            text = r.text
            stat = r.status_code
            dsl = DslStats('test',text) 
            csv_path = os.path.join(COLLATE_IN, "dsl_stats.csv")
            with open(csv_path, "a") as fh:
                fh.write("{}\n".format(dsl.as_csv()))



    def modals(self):
        with open("vf.modals.{}.log".format(int(time.time())), "w") as modals_fh:
            info_map = {
                    "status=systemInfo" : "systemInfo",
                    "status=wifiInfo" : "wifiInfo",
                    "status=networkInfo" : "networkInfo",
                    "status=arp" : "arp",

                    }
            base_url="http://vodafone.broadband/modals/status-support/status.lp?status=systemInfo"
            for (uarg, ulabel) in info_map.items():
                self.driver.get(base_url.format(uarg))
                time.sleep(2)
                modals_fh.write("{}\n".format(ulabel))
                modals_fh.write("{}\n".format(self.driver.page_source))
                modals_fh.write("-"*50+"\n")
            more_stuff = """
            base_url="http://vodafone.broadband/home.lp?getSessionStatus=true"
            for (uarg, ulabel) in info_map.items():
                self.driver.get(base_url.format(uarg))
                time.sleep(2)
                modals_fh.write("{}\n".format(ulabel))
                modals_fh.write("{}\n".format(self.driver.page_source))
                modals_fh.write("-"*50+"\n")
            base_url="http://vodafone.broadband/modals/status-support/lhhome.lp?getSessionStatus=true"
            for (uarg, ulabel) in info_map.items():
                self.driver.get(base_url.format(uarg))
                time.sleep(2)
                modals_fh.write("{}\n".format(ulabel))
                modals_fh.write("{}\n".format(self.driver.page_source))
                modals_fh.write("-"*50+"\n")
            """

    def download_syslog(self, timeout = 10):
        #time.sleep(timeout)
        t1 = time.time()
        _LOGGER.info("Try to click on StatusSupport at {} since start".format(t1-self.t0))
        #pdb.set_trace()
        # Some tactics to be able to interact with it
        wait = WebDriverWait(self.driver, 40)
        wait.until(EC.element_to_be_clickable((By.ID, "StatusSupport")))
        _LOGGER.info("Waited until clickable")
        elem = self.driver.find_element_by_id("StatusSupport")
        _LOGGER.info("Retrieved the element")
        elem.click()
        _LOGGER.info("Clicked it")
        wait.until(EC.element_to_be_clickable((By.ID, "event-log")))
        #pdb.set_trace()
        syslog_button = self.find_by_id("event-log", 5)
        time.sleep(3)
        syslog_button.click()
        wait.until(EC.element_to_be_clickable((By.ID, "elog-btn-download")))
        time.sleep(10)
        download_button = self.find_by_id("elog-btn-download", 5)
        download_button.click()
        time.sleep(5)

def remainder():
    driver.find_element_by_id("login-btn-logIn").click()
    time.sleep(15)
    driver.find_element_by_id("StatusSupport").click()
    time.sleep(15)
    driver.find_element_by_id("event-log").click()
    time.sleep(15)
    driver.find_element_by_id("elog-btn-download").click()


def test_nowait(pwd):
    try:
        v = VodafoneMonitor(with_chrome = True)
        v.authenticate(pwd=pwd)
    finally:
        v.driver.quit()
    _LOGGER.info("NBo wait browser done")

def test_explicit_wait(pwd,timeout):
    try:
        v = VodafoneMonitor(with_chrome = True)
        v.authenticate_wait_explicit(pwd=pwd,timeout=timeout)
        v.modals_request()
        v.download_syslog(timeout=timeout)
    finally:
        v.driver.quit()
    _LOGGER.info("Explicit wait browser done")


def wait_for_syslog_download():
    i = inotify.adapters.Inotify()
    i.add_watch("/home/astephen/Downloads/")
    _LOGGER.info("watching Downloads")
    try:
        for event in i.event_gen():
            _LOGGER.debug("inotify event")
            if event is not None:
                (header, type_names, watch_path, filename) = event
                _LOGGER.info("File {} created".format(filename))
            pdb.set_trace()
            if os.path.exists(DOWNLOAD_TARGET): print("{} ready to move".format(DOWNLOAD_TARGET))
    finally:
        i.remove_watch("/home/astephen/Downloads")


DOWNLOAD_TARGET="/home/astephen/Downloads/syslog.log"


def rotate_syslog():
    if os.path.exists(DOWNLOAD_TARGET):
        move_path = os.path.join(COLLATE_IN, "syslog.{}.log".format(int(time.time())))
        if os.path.exists(move_path):
            raise ValueError("Unexpected name clash for {}".format(move_path))
        else:
            shutil.move(DOWNLOAD_TARGET, move_path)
            _LOGGER.info("syslog.log renamed to {}".format(move_path))
    else:
        _LOGGER.debug("{} not ready for move".format(DOWNLOAD_TARGET))

# TODO : add diff and patch functionality to build ever bigger syslog history

def _configure_logging():
    _LOGGER.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    _LOGGER.addHandler(ch)


if __name__ == '__main__':
    _configure_logging()
    pwd = sys.argv[1]
    test_explicit_wait(pwd, 10)
    _LOGGER.info("monitor_thread running")
    time.sleep(5)
    rotate_syslog()
    _LOGGER.info("Complete")

    #session cookie was
    #b580083856dbf980421a00948c05db4fa061aa17650d4f7cfc6fc0bd6cf28ad6

    # TODO : test if we can replay the cookie with requests, say ?

    # The cookie name is sessionID

