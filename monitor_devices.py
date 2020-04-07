#!/usr/bin/python3

###############################################################################################################
# Language     :  Python (3.7)
# Filename     :  monitore_devices.py
# Autor        :  https://github.com/nosari20
# Description  :  Nagios/Centreon plugin for MobileIron Core Devices
# Repository   :  https://github.com/nosari20/centreon-mobileiron-plugin
###############################################################################################################
#
# Return code
#
#   |  Return Code  |       State        
#   |      0        |         OK	     
#   |      1        |       WARNING	     
#   |      2        |       CRITICAL	 
#   |      3        |       UNKNOWN	     
#
### Changelog ###
#
# ~~ Version 0.1 ~~
#
#
###############################################################################################################

import argparse
import json
import math
from utils import api_util


# Command line parser setup
usage = '%(prog)s <host> <command> [options]'
description = 'Nagios/Centreon plugin for MobileIron Core Devices'
parser = argparse.ArgumentParser(description=description, usage=usage)


# Args
parser.add_argument('host',
                    metavar='host', 
                    type=str,
                    help='Host FQDN of IP')

parser.add_argument('command',
                    metavar='command', 
                    type=str,
                    choices=['active', 'non-compliant', 'quarantined', 'filter'],
                    help='Available commands: active, non-compliant, quarantined, filter (custom search filter)')


# API options
group_api = parser.add_argument_group('API options')

group_api.add_argument('--api-username',
                    dest='api_username',
                    type=str,  
                    default='',
                    help='API Username')

group_api.add_argument('--api-password',
                    dest='api_password',
                    type=str,  
                    default='',
                    help='API Password')

group_api.add_argument('--api-filter',
                    dest='api_filter',
                    type=str,  
                    default='',
                    help='API device filter')

group_api.add_argument('--api-port',
                    dest='api_port',
                    type=int,  
                    default=443,
                    help='API port (default: 443)')

# Monitoring options
group_general = parser.add_argument_group('Monitoring')
parser.add_argument('--warning',
                    dest='warning',
                    type=int,
                    default=None,
                    help='Warning threshold (if applicable)')

parser.add_argument('--critical',
                    dest='critical',
                    type=int,
                    default=None,
                    help='Critical threshold (if applicable)')

parser.add_argument('--maximum-devices',
                    dest='maximum_devices',
                    type=int,
                    default=5000,
                    choices=[5000, 20000, 50000, 100000],
                    help='Maximum number od devices supported (5 000, 20 000, 50 000, 100 000)')

def service_output(title: str, exit_code: int, message: str, perfdata: str = None):
    status = 'UNKNOWN'
    if exit_code == 0:
        status = "OK"
    if exit_code == 1:
        status = "WARNING"
    if exit_code == 2:
        status = "CRITICAL"
    print("{} {} - {};{}".format(title, status, message, ('|'+perfdata if perfdata != None else '')))
    exit(exit_code)


# Command line parser
args = parser.parse_args()

# All Devices
if args.command == 'active':

    if args.api_username == '' or args.api_password == '':
        service_output(
            title = 'ACTIVE DEVICES',
            exit_code = 3,
            message = 'API username and password required'
        )
    
    success, result = api_util.core_api(
        host = args.host,
        request = 'devices/count?adminDeviceSpaceId=1&query="common.status"="ACTIVE"',
        username = args.api_username,
        password = args.api_password
    )

    if not success :
        service_output(
            title = 'ACTIVE DEVICES',
            exit_code = 3,
            message = result
        )

    active_devices = int(json.loads(result)['totalCount'])

    warning_threshold = (args.warning if args.warning != None else 90)
    critical_threshold = (args.critical if args.critical != None else 100)

    exit_code = 0
    if active_devices >= int(warning_threshold / 100 * args.maximum_devices) :
        exit_code = 1
    if active_devices >= int(critical_threshold / 100 * args.maximum_devices) :
        exit_code = 2
    
    service_output(
        title = 'ACTIVE DEVICES',
        exit_code = exit_code,
        message = 'Number of Active devices : {}'.format(active_devices),
        perfdata = '\'devices\'={}devices;{};{};{};{};'.format(
            active_devices,
            int(warning_threshold / 100 * args.maximum_devices),
            int(critical_threshold / 100 * args.maximum_devices),
            0,
            args.maximum_devices)
    )

if args.command == 'non-compliant':
    if args.api_username == '' or args.api_password == '':
        service_output(
            title = 'NON-COMPLIANT DEVICES',
            exit_code = 3,
            message = 'API username and password required'
        )
    
    success, result = api_util.core_api(
        host = args.host,
        request = 'devices/count?adminDeviceSpaceId=1&query="common.status"="ACTIVE"',
        username = args.api_username,
        password = args.api_password
    )

    if not success :
        service_output(
            title = 'NON-COMPLIANT DEVICES',
            exit_code = 3,
            message = result
        )

    active_devices = int(json.loads(result)['totalCount'])

    success, result = api_util.core_api(
        host = args.host,
        request = 'devices/count?adminDeviceSpaceId=1&query="common.status"="ACTIVE" AND "common.compliant" = false',
        username = args.api_username,
        password = args.api_password
    )

    nc_devices = int(json.loads(result)['totalCount'])

    if not success :
        service_output(
            title = 'NON-COMPLIANT DEVICES',
            exit_code = 3,
            message = result
        )

    warning_threshold = (args.warning if args.warning != None else 5)
    critical_threshold = (args.critical if args.critical != None else 10)

    exit_code = 0
    if nc_devices >= math.ceil(warning_threshold / 100 * active_devices) :
        exit_code = 1
    if nc_devices >= math.ceil(critical_threshold / 100 * active_devices) :
        exit_code = 2
    
    service_output(
        title = 'NON-COMPLIANT DEVICES',
        exit_code = exit_code,
        message = 'Number of Non-compliant devices : {} ({}%)'.format(nc_devices, int(nc_devices/active_devices*100)),
        perfdata = '\'devices\'={}devices;{};{};{};{};'.format(
            nc_devices,
            math.ceil(warning_threshold / 100 * active_devices),
            math.ceil(critical_threshold / 100 * active_devices),
            0,
            args.maximum_devices)
    )

if args.command == 'quarantined':
    if args.api_username == '' or args.api_password == '':
        service_output(
            title = 'QUARANTINED DEVICES',
            exit_code = 3,
            message = 'API username and password required'
        )
    
    success, result = api_util.core_api(
        host = args.host,
        request = 'devices/count?adminDeviceSpaceId=1&query="common.status"="ACTIVE"',
        username = args.api_username,
        password = args.api_password
    )

    if not success :
        service_output(
            title = 'QUARANTINED DEVICES',
            exit_code = 3,
            message = result
        )

    active_devices = int(json.loads(result)['totalCount'])

    success, result = api_util.core_api(
        host = args.host,
        request = 'devices/count?adminDeviceSpaceId=1&query="common.status"="ACTIVE" AND "common.quarantined" = true',
        username = args.api_username,
        password = args.api_password
    )

    quarantined_devices = int(json.loads(result)['totalCount'])

    if not success :
        service_output(
            title = 'QUARANTINED DEVICES',
            exit_code = 3,
            message = result
        )

    warning_threshold = (args.warning if args.warning != None else 5)
    critical_threshold = (args.critical if args.critical != None else 10)

    exit_code = 0
    if quarantined_devices >= math.ceil(warning_threshold / 100 * active_devices) :
        exit_code = 1
    if quarantined_devices >= math.ceil(critical_threshold / 100 * active_devices) :
        exit_code = 2
    
    service_output(
        title = 'QUARANTINED DEVICES',
        exit_code = exit_code,
        message = 'Number of quarantined devices : {} ({}%)'.format(quarantined_devices, int(quarantined_devices/active_devices*100)),
        perfdata = '\'devices\'={}devices;{};{};{};{};'.format(
            quarantined_devices,
            math.ceil(warning_threshold / 100 * active_devices),
            math.ceil(critical_threshold / 100 * active_devices),
            0,
            args.maximum_devices)
    )

if args.command == 'filter':
    if args.api_username == '' or args.api_password == '':
        service_output(
            title = 'DEVICES',
            exit_code = 3,
            message = 'API username and password required'
        )
    
    if args.api_filter == '':
        service_output(
            title = 'DEVICES',
            exit_code = 3,
            message = 'Filter required'
        )
    
    success, result = api_util.core_api(
        host = args.host,
        request = 'devices/count?adminDeviceSpaceId=1&query="common.status"="ACTIVE"',
        username = args.api_username,
        password = args.api_password
    )

    if not success :
        service_output(
            title = 'QUARANTINED DEVICES',
            exit_code = 3,
            message = result
        )

    active_devices = int(json.loads(result)['totalCount'])

    success, result = api_util.core_api(
        host = args.host,
        request = 'devices/count?adminDeviceSpaceId=1&query={}'.format(args.api_filter),
        username = args.api_username,
        password = args.api_password
    )

    devices = int(json.loads(result)['totalCount'])

    if not success :
        service_output(
            title = 'DEVICES',
            exit_code = 3,
            message = result
        )

    warning_threshold = (args.warning if args.warning != None else 5)
    critical_threshold = (args.critical if args.critical != None else 10)

    exit_code = 0
    if devices >= math.ceil(warning_threshold / 100 * active_devices) :
        exit_code = 1
    if devices >= math.ceil(critical_threshold / 100 * active_devices) :
        exit_code = 2
    
    service_output(
        title = 'DEVICES',
        exit_code = exit_code,
        message = 'Number of devices : {} ({}%)'.format(devices, int(devices/active_devices*100)),
        perfdata = '\'devices\'={}devices;{};{};{};{};'.format(
            devices,
            math.ceil(warning_threshold / 100 * active_devices),
            math.ceil(critical_threshold / 100 * active_devices),
            0,
            args.maximum_devices)
    )


