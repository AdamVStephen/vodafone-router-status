import datetime
import re
import json
import unittest
import pdb

from collections import OrderedDict

from bs4 import BeautifulSoup

statPat = re.compile('''.*{"systemParams":({.*})}.*''')

class SystemStats:
    """Parser for the return data from the Vodafone router."""

    def __init__(self, desc, text):
        """text is the html returned by requests.get().text."""
        self.desc = desc
        self.text = text
        self.json = None
        m = statPat.match(text)
        if m:
            self.json = json.loads(m.group(1))
            self.dict = dict(self.json)

    def as_csv(self):
        """Key statistics returned as a CSV row for logging."""
        keys = ['sys_time', 'sys_uptime', 'sys_mem_usage', 'sys_mem_total', 'sys_reboot_cause', 'sys_cpu_usage']
        vals = [self.dict.get(k) for k in keys]
        return ','.join(vals)

    def __repr__(self):
        if self.json is None: 
            return self
        else:
            return "{}\n{}".format(self.desc, json.dumps(self.json, indent=4, sort_keys=True))


test_data = {
        "systemInfo" : '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"systemParams":{"sys_hw_version":"Vox3.0v","sys_bootloader_version":"19.02.1146-0000000-20190110090550-897d2844f012557134a272eb8a8a90f85e9a7a8d","sys_uptime":"9 days, 7 hours, 52 minutes and 8 seconds","sys_mem_usage":"77","sys_mem_total":"432928","sys_wireless_driver_version5GHz":"7.14.170.36","sys_time":"21.02.2021 | 5:58 pm","sys_wireless_driver_version24GHz":"7.14.170.36","sys_gw_version":"19.2.0307-3261013-20200812152603-87d129527e2b6c5db641b036118778179b03c3da","sys_reboot_cause":"System Self","sys_cpu_usage":"4","imeisv":"0","sys_gw_serial":"CP2022RAGCL"}}</pre></body></html>',

    "wifiInfo" : '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"systemParams":{"sys_hw_version":"Vox3.0v","sys_bootloader_version":"19.02.1146-0000000-20190110090550-897d2844f012557134a272eb8a8a90f85e9a7a8d","sys_uptime":"9 days, 7 hours, 52 minutes and 11 seconds","sys_mem_usage":"77","sys_mem_total":"432928","sys_wireless_driver_version5GHz":"7.14.170.36","sys_time":"21.02.2021 | 5:58 pm","sys_wireless_driver_version24GHz":"7.14.170.36","sys_gw_version":"19.2.0307-3261013-20200812152603-87d129527e2b6c5db641b036118778179b03c3da","sys_reboot_cause":"System Self","sys_cpu_usage":"0","imeisv":"0","sys_gw_serial":"CP2022RAGCL"}}</pre></body></html>',

    "networkInfo" : '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"systemParams":{"sys_hw_version":"Vox3.0v","sys_bootloader_version":"19.02.1146-0000000-20190110090550-897d2844f012557134a272eb8a8a90f85e9a7a8d","sys_uptime":"9 days, 7 hours, 52 minutes and 17 seconds","sys_mem_usage":"77","sys_mem_total":"432928","sys_wireless_driver_version5GHz":"7.14.170.36","sys_time":"21.02.2021 | 5:59 pm","sys_wireless_driver_version24GHz":"7.14.170.36","sys_gw_version":"19.2.0307-3261013-20200812152603-87d129527e2b6c5db641b036118778179b03c3da","sys_reboot_cause":"System Self","sys_cpu_usage":"4","imeisv":"0","sys_gw_serial":"CP2022RAGCL"}}</pre></body></html>', 

    "arpInfo" : '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"systemParams":{"sys_hw_version":"Vox3.0v","sys_bootloader_version":"19.02.1146-0000000-20190110090550-897d2844f012557134a272eb8a8a90f85e9a7a8d","sys_uptime":"9 days, 7 hours, 52 minutes and 24 seconds","sys_mem_usage":"77","sys_mem_total":"432928","sys_wireless_driver_version5GHz":"7.14.170.36","sys_time":"21.02.2021 | 5:59 pm","sys_wireless_driver_version24GHz":"7.14.170.36","sys_gw_version":"19.2.0307-3261013-20200812152603-87d129527e2b6c5db641b036118778179b03c3da","sys_reboot_cause":"System Self","sys_cpu_usage":"0","imeisv":"0","sys_gw_serial":"CP2022RAGCL"}}</pre></body></html>'
        }


class TestSystemStats(unittest.TestCase):

    def test_parser(self):
        for (key, data) in test_data.items():
            ss = SystemStats(key, data)
            self.assertTrue(ss.json is not None)
            print(ss)
            print(ss.as_csv())

uptime_pat = re.compile('''([0-9]+ weeks?,)?\s*([0-9]+ days?,)?\s*([0-9]+ hours?,)?\s*([0-9]+ minutes?)?\s*(?:and)?\s*([0-9]+ seconds?)''')
number_then_pat = re.compile('''\s*([0-9]+)\s*([^0-9]+)''')
time_groups = OrderedDict()
time_groups["weeks"] = lambda s : extract_count(s)*7
time_groups["days"] = lambda s : extract_count(s)
time_groups["hours"] = lambda s : extract_count(s)*3600
time_groups["minutes"] = lambda s : extract_count(s)*60
time_groups["seconds"] = lambda s : extract_count(s)

def extract_count(str):
    try:
        m = number_then_pat.match(str)
        if m:
            count = int(m.group(1))
        else:
            count = 0
    except:
        count = 0
    return count

def uptime_timedelta(uptime):
    m = uptime_pat.match(uptime)
    #pdb.set_trace()
    if m:
        elements = m.groups()
        weeks = extract_count(elements[0]) if elements[0] is not None else 0
        days = extract_count(elements[1]) if elements[1] is not None else 0
        hours = extract_count(elements[2]) if elements[2] is not None else 0
        minutes = extract_count(elements[3]) if elements[3] is not None else 0
        seconds = extract_count(elements[4]) if elements[4] is not None else 0
        #
        interval = datetime.timedelta(weeks = weeks, days=days, hours = hours, minutes = minutes, seconds=seconds)
        return interval


def wdhms_td(wdhms):
    return datetime.timedelta(weeks = wdhms[0], days = wdhms[1], hours = wdhms[2], minutes = wdhms[3], seconds=wdhms[4])

uptime_test_data = {
        "5 days, 11 hours, 12 minutes and 37 seconds" : wdhms_td([0, 5,11,12,37]),
        "2 weeks, 5 days, 11 hours, 12 minutes and 37 seconds" : wdhms_td([2,5,11,12,37]),
        "33 seconds" : wdhms_td([0,0,0,0,33]),
        "10 minutes and 47 seconds" : wdhms_td([0,0,0,10,47]),
        "1 hour, 15 minutes and 6 seconds" : wdhms_td( [0,0,1,15,6]),
        "16 hour, 42 minutes and 59 seconds" : wdhms_td([0,0,16,42,59]),
        "1 day, 11 hours, 12 minutes and 37 seconds" : wdhms_td( [0,1,11,12,37])
        }

class TestUptimeToSeconds(unittest.TestCase):

    def test_times(self):
        for (text, td) in uptime_test_data.items():
            result = uptime_timedelta(text)
            #pdb.set_trace()
            self.assertEqual(result, td)


class DslStats:
    """Parser for the return data from the Vodafone router."""

    def __init__(self, desc, text):
        """text is the html returned by requests.get().text."""
        self.desc = desc
        self.text = text
        soup = BeautifulSoup(text)
        uptime = soup.find(id='adslStat_info_uptime')
        if uptime is not None:
            self.uptime = uptime.text
            self.uptime_interval = uptime_timedelta(self.uptime)
            self.uptime_days = "{}".format(round(self.uptime_interval.total_seconds()/(24*3600),2))
        tables = soup.find_all('table')
        dsl_table = tables[0]
        data = dsl_table.find_all('td')
        self.download_rate = data[1].text
        self.upload_rate = data[2].text
        self.download_max = data[4].text
        self.upload_max = data[5].text
        self.json = None

    def as_csv(self):
        """Key statistics returned as a CSV row for logging."""
        keys = ['uptime_days', 'uptime', 'download_rate', 'upload_rate', 'download_max', 'upload_max']
        vals = [self.__getattribute__(k) for k in keys]
        return ','.join(vals)

    def __repr__(self):
        if self.json is None: 
            return self.as_csv()
        else:
            return "{}\n{}".format(self.desc, json.dumps(self.json, indent=4, sort_keys=True))


dsl_test_data = {
        "systemInfo" : '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"systemParams":{"sys_hw_version":"Vox3.0v","sys_bootloader_version":"19.02.1146-0000000-20190110090550-897d2844f012557134a272eb8a8a90f85e9a7a8d","sys_uptime":"9 days, 7 hours, 52 minutes and 8 seconds","sys_mem_usage":"77","sys_mem_total":"432928","sys_wireless_driver_version5GHz":"7.14.170.36","sys_time":"21.02.2021 | 5:58 pm","sys_wireless_driver_version24GHz":"7.14.170.36","sys_gw_version":"19.2.0307-3261013-20200812152603-87d129527e2b6c5db641b036118778179b03c3da","sys_reboot_cause":"System Self","sys_cpu_usage":"4","imeisv":"0","sys_gw_serial":"CP2022RAGCL"}}</pre></body></html>',

    "wifiInfo" : '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"systemParams":{"sys_hw_version":"Vox3.0v","sys_bootloader_version":"19.02.1146-0000000-20190110090550-897d2844f012557134a272eb8a8a90f85e9a7a8d","sys_uptime":"9 days, 7 hours, 52 minutes and 11 seconds","sys_mem_usage":"77","sys_mem_total":"432928","sys_wireless_driver_version5GHz":"7.14.170.36","sys_time":"21.02.2021 | 5:58 pm","sys_wireless_driver_version24GHz":"7.14.170.36","sys_gw_version":"19.2.0307-3261013-20200812152603-87d129527e2b6c5db641b036118778179b03c3da","sys_reboot_cause":"System Self","sys_cpu_usage":"0","imeisv":"0","sys_gw_serial":"CP2022RAGCL"}}</pre></body></html>',

    "networkInfo" : '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"systemParams":{"sys_hw_version":"Vox3.0v","sys_bootloader_version":"19.02.1146-0000000-20190110090550-897d2844f012557134a272eb8a8a90f85e9a7a8d","sys_uptime":"9 days, 7 hours, 52 minutes and 17 seconds","sys_mem_usage":"77","sys_mem_total":"432928","sys_wireless_driver_version5GHz":"7.14.170.36","sys_time":"21.02.2021 | 5:59 pm","sys_wireless_driver_version24GHz":"7.14.170.36","sys_gw_version":"19.2.0307-3261013-20200812152603-87d129527e2b6c5db641b036118778179b03c3da","sys_reboot_cause":"System Self","sys_cpu_usage":"4","imeisv":"0","sys_gw_serial":"CP2022RAGCL"}}</pre></body></html>', 

    "arpInfo" : '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"systemParams":{"sys_hw_version":"Vox3.0v","sys_bootloader_version":"19.02.1146-0000000-20190110090550-897d2844f012557134a272eb8a8a90f85e9a7a8d","sys_uptime":"9 days, 7 hours, 52 minutes and 24 seconds","sys_mem_usage":"77","sys_mem_total":"432928","sys_wireless_driver_version5GHz":"7.14.170.36","sys_time":"21.02.2021 | 5:59 pm","sys_wireless_driver_version24GHz":"7.14.170.36","sys_gw_version":"19.2.0307-3261013-20200812152603-87d129527e2b6c5db641b036118778179b03c3da","sys_reboot_cause":"System Self","sys_cpu_usage":"0","imeisv":"0","sys_gw_serial":"CP2022RAGCL"}}</pre></body></html>'
        }


class TestDslStats(unittest.TestCase):

    def test_parser(self):
        print("Dsl")
        with open("dsl.text", "r") as fh:
            text = fh.read()
        pdb.set_trace()
        dslStats = DslStats('stuff', text)
        print(dslStats)
        print(dslStats.as_csv)

if __name__ == '__main__':
    tests = []
    #tests.append("TestSystemStats")
    tests.append("TestDslStats")
    tests.append("TestUptimeToSeconds")
    unittest.main(defaultTest=tests)

