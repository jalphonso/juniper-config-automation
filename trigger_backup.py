from junos import Junos_Context
from junos import Junos_Trigger_Event
from junos import Junos_Received_Events
from jnpr.junos import Device
import jcs
import requests
import sys
import urllib3


if __name__ == '__main__':
    hostname = Junos_Context['hostname']
    try:
        url = None
        token = None

        arg1 = sys.argv[1]
        if arg1 == '-url':
            url = sys.argv[2]
        elif arg1 == '-token':
            token = sys.argv[2]

        arg2 = sys.argv[3]
        if arg2 == '-url':
            url = sys.argv[4]
        elif arg2 == '-token':
            token = sys.argv[4]

        if not url or not token:
            jcs.syslog("change.error", "Missing url or token args")
            raise Exception

        jcs.syslog("change.info", f"hostname: {hostname}\nurl: {url}\ntoken: {token}\n")
        message = Junos_Received_Events.xpath('//received-event/message')[0].text
        body = {
            "action": "backup",
            "token": token,
            "server": hostname,
            "comment": message
        }
        urllib3.disable_warnings()
        resp = requests.post(url=url, json=body, verify=False)
        jcs.syslog("change.info", f"Webhook response code: {resp.status_code}")
    except Exception:
        jcs.syslog("missing one or more args. required args are 'url' and 'token'")
