#!/usr/bin/env python

import datetime
import json
import re
import requests
import sys
import traceback

APIUrl = 'https://dns.api.gandi.net/api/v5'
configFilename = './gandi-dyndns.json'
requestTimeout = 5


def log(msg):
    now = datetime.datetime.now()
    print('{0}: {1}'.format(now, msg))


def read_config():
    config = json.load(open(configFilename))
    return config['APIKey'], config['domain'], config['lastIP'], config['records']


def update_config_last_ip(address):
    with open(configFilename) as f:
        content = f.read()

    new_content = re.sub(r'"lastIP": "\d+.\d+.\d+.\d+",', r'"lastIP": "' + address + '",', content)

    with open(configFilename, 'w') as f:
        f.write(new_content)


def get_public_ip():
    r = requests.get('https://ip4.seeip.org', timeout=requestTimeout)
    r.raise_for_status()
    return r.text


def update_records_address(records, address):
    for r in records:
        r['rrset_values'] = [address]


def set_records(domain, api_key, records):
    headers = {'X-API-KEY': api_key}

    for r in records:
        name = r['rrset_name']
        address_type = r['rrset_type']
        url = APIUrl + '/domains/' + domain + '/records/' + name + '/' + address_type

        try:
            r = requests.put(url, json=r, headers=headers, timeout=requestTimeout)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            log('Failed to update record: {0}'.format(e))


def main():
    try:
        force = len(sys.argv) == 2 and sys.argv[1] == '-f'
        api_key, domain, last_ip, records = read_config()
        current_ip = get_public_ip()

        if force or last_ip != current_ip:
            log('IP address changed from {0} to {1}, updating records'.format(last_ip, current_ip))
            update_records_address(records, current_ip)
            set_records(domain, api_key, records)
            update_config_last_ip(current_ip)
    except Exception as e:
        log('An error occurred: {0}'.format(e))
        traceback.print_exc()


main()
