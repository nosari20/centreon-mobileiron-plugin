#!/usr/bin/python3

###############################################################################################################
# Language     :  Python (3.7)
# Filename     :  monitore_sentry.py
# Autor        :  https://github.com/nosari20
# Description  :  Nagios/Centreon plugin for MobileIron Sentry
# Repository   :  https://github.com/nosari20/centreon-mobileiron-plugin
###############################################################################################################
#
# Return code
#
#   |  Return Code  |   Service State    |   Host State
#   |      0        |         OK	     |      UP
#   |      1        |       WARNING	     |      UP
#   |      2        |       CRITICAL	 |   DOWN/UNREACHABLE
#   |      3        |       UNKNOWN	     |   DOWN/UNREACHABLE
#
### Changelog ###
#
# ~~ Version 0.1 ~~
#
#
###############################################################################################################

import argparse
import datetime
import math
import json
import re
from utils import cert_util, snmp_util, tcp_util, mics_util


# Command line parser setup
usage = '%(prog)s <host> <command> [options]'
description = 'Nagios/Centreon plugin for MobileIron Sentry'
parser = argparse.ArgumentParser(description=description, usage=usage)


# Args
parser.add_argument('host',
                    metavar='host', 
                    type=str,
                    help='Host FQDN of IP')

parser.add_argument('command',
                    metavar='command', 
                    type=str,
                    choices=['tcp_ping', 'certificate', 'storage', 'memory', 'cpu', 'uptime', 'logging', 'dns', 'ntp', 'devices'],
                    help='Available commands: tcp_ping, certificate, storage, memory, cpu, uptime, logging, dns, ntp, devices')


# General options
group_general = parser.add_argument_group('General')

group_general.add_argument('--sentry-port',
                    dest='sentry_port',
                    type=int,  
                    default=443,
                    choices=[443, 8443],
                    help='Sentry port (default: 443)')

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

# TCP ping
group_tcp = parser.add_argument_group('Options for tcp ping')

group_tcp.add_argument('--tcp-attempt',
                    dest='tcp_attempt',
                    type=int,  
                    default=20,
                    help='TCP sync attempt (default: 20)')

group_tcp.add_argument('--tcp-failed-warning',
                    dest='tcp_failed_warning',
                    type=int,  
                    default=50,
                    help='Warning threshold for failed attempt (default: 30%)')

group_tcp.add_argument('--tcp-failed-critical',
                    dest='tcp_failed_critical',
                    type=int,  
                    default=100,
                    help='Critical threshold for failed attempt (default: 100)')

# SNMP check
group_snmp = parser.add_argument_group('SNMP options')

group_snmp.add_argument('--snmp-community',
                    dest='snmp_community',
                    type=str,  
                    default='public',
                    help='SNMP community (default: \'public\')')

group_snmp.add_argument('--snmp-version',
                    dest='snmp_version',
                    type=int,  
                    default=1,
                    help='SNMP version [0:v1, 1:v2] (default: \'v2\')')

# MICS
group_mics = parser.add_argument_group('MICS options')

group_mics.add_argument('--mics-username',
                    dest='mics_username',
                    type=str,  
                    default='admin',
                    help='MICS username (default: \'admin\')')

group_mics.add_argument('--mics-password',
                    dest='mics_password',
                    type=str,
                    default='',
                    help='MICS password')


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

# TCP ping
if args.command == 'tcp_ping':
    
    success, time, passed, failed, error = tcp_util.tcp_ping(
        host = args.host,
        port = args.sentry_port,
        timeout = 1,
        packets = args.tcp_attempt
    )
    

    if not success :
        service_output(
        title = 'TCP PORT {}'.format(args.sentry_port),
        exit_code = 3, 
        message = error
    )

    warning_threshold = (args.warning if args.warning != None else 1000)
    critical_threshold =(args.critical if args.critical != None else 2000)

    exit_code = 0
    if time >= warning_threshold :
        exit_code = 1
    if time >= critical_threshold :
        exit_code = 2

    if failed > args.tcp_failed_warning :
        exit_code = 1
    if failed > args.tcp_failed_critical :
        exit_code = 2

    service_output(
        title = 'TCP PORT {}'.format(args.sentry_port),
        exit_code = exit_code, 
        message = 'time={}ms passed={} failed={}'.format(int(time), passed, failed ),
        perfdata = '\'time\'={}ms;{};{};{};{};'.format(
            int(time),
            warning_threshold,
            critical_threshold,
            0,
            int(critical_threshold*1.5)) 
            
            +

            '\'failed\'={}%;{};{};{};{};'.format(
                int(failed/(passed+failed)*100),
                args.tcp_failed_warning,
                args.tcp_failed_critical,
                0,
                100)
    )

###############################################################################################################

# SSL check
if args.command == 'certificate':
    
    success, remaining_days, message = cert_util.check_cert(
        host = args.host,
        port = args.sentry_port
    )
    
    if not success :
        service_output(
        title = 'CERTIFICATE PORT {}'.format(args.sentry_port),
        exit_code = 3, 
        message = message
    )

    warning_threshold = (args.warning if args.warning != None else 60)
    critical_threshold =(args.critical if args.critical != None else 30)

    exit_code = 0
    if remaining_days < warning_threshold :
        exit_code = 1
    if remaining_days < critical_threshold :
        exit_code = 2
    
    service_output(
        title = 'CERTIFICATE PORT {}'.format(args.sentry_port),
        exit_code = exit_code, 
        message = message
    )

###############################################################################################################   

# Storage check
if args.command == 'storage':
    
    prefix = 'iso.org.dod.internet.mgmt.mib-2.25.2.3.'

    hrStorageDescr_OID = prefix + '1.3'
    hrStorageAllocationUnits_OID = prefix + '1.4'
    hrStorageSize_OID = prefix + '1.5'
    hrStorageUsed_OID = prefix + '1.6'

    success, result, message = snmp_util.snmp_table(
        host = args.host,
        oids = [
            hrStorageDescr_OID,
            hrStorageAllocationUnits_OID,
            hrStorageSize_OID,
            hrStorageUsed_OID
        ],
        version = args.snmp_version,
        community = args.snmp_community
    )
  
    if not success :
        service_output(
            title = 'STORAGE',
            exit_code = 3,
            message = message
        )


    storage_table = dict()
    for storage in result :
        
        hrStorageDescr = storage[hrStorageDescr_OID]
        hrStorageAllocationUnits = int(storage[hrStorageAllocationUnits_OID])
        hrStorageSize = int(storage[hrStorageSize_OID]) * hrStorageAllocationUnits
        hrStorageUsed = int(storage[hrStorageUsed_OID]) * hrStorageAllocationUnits
        hrStorageUsedPercent = round(hrStorageUsed/hrStorageSize*100,1)

        storage_table[hrStorageDescr] = {
            'hrStorageDescr' : hrStorageDescr,
            'hrStorageAllocationUnits' : hrStorageAllocationUnits,
            'hrStorageSize' : hrStorageSize,
            'hrStorageUsed' : hrStorageUsed,
            'hrStorageUsedPercent' : hrStorageUsedPercent,
        }

        

    warning_threshold = (args.warning if args.warning != None else 70)
    critical_threshold = (args.critical if args.critical != None else 90)
    exit_code = 0
    if storage_table['/']['hrStorageUsedPercent'] >= warning_threshold:
        exit_code = 1
    if storage_table['/']['hrStorageUsedPercent'] >= critical_threshold:
        exit_code = 2



    perfdata = '\'/\'={}B;{};{};{};{};'.format(
            hrStorageUsed,
            round(warning_threshold*hrStorageSize/100),
            round(critical_threshold*hrStorageSize/100),
            0,
            hrStorageSize)

    for hrStorageDescr in storage_table :
        if hrStorageDescr.startswith('/') and hrStorageDescr != '/' :
            perfdata += '\'{}\'={}B;{};{};{};{},'.format(
                            hrStorageDescr,
                            storage_table[hrStorageDescr]['hrStorageUsed'],
                            '',
                            '',
                            0,
                            storage_table[hrStorageDescr]['hrStorageSize'])
    
    service_output(
        title = 'STORAGE',
        exit_code = exit_code,
        message = 'Used: {}/{}GB ({}%)'.format(round(storage_table['/']['hrStorageUsed'] * 10**-9,1), round(storage_table['/']['hrStorageSize'] * 10**-9,1), storage_table['/']['hrStorageUsedPercent']),
        perfdata = perfdata
    )

###############################################################################################################

# Memory check
if args.command == 'memory':
    
    prefix = 'iso.org.dod.internet.mgmt.mib-2.25.2.3.'

    hrStorageAllocationUnits_OID = prefix + '1.4.1'
    hrStorageSize_OID = prefix + '1.5.1'
    hrStorageUsed_OID = prefix + '1.6.1'

    success, result, message = snmp_util.snmp_get(
        host = args.host,
        oids = [
            hrStorageAllocationUnits_OID,
            hrStorageSize_OID,
            hrStorageUsed_OID
        ],
        version = args.snmp_version,
        community = args.snmp_community
    )

    if not success :
        service_output(
            title = 'MEMORY',
            exit_code = 3,
            message = message
        )

    hrStorageAllocationUnits = int(result[hrStorageAllocationUnits_OID])
    hrStorageSize = int(result[hrStorageSize_OID]) * hrStorageAllocationUnits
    hrStorageUsed = int(result[hrStorageUsed_OID]) * hrStorageAllocationUnits
    hrStorageUsedPercent = round(hrStorageUsed/hrStorageSize*100,1)

    warning_threshold = (args.warning if args.warning != None else 90)
    critical_threshold = (args.critical if args.critical != None else 100)

    exit_code = 0
    if hrStorageUsedPercent >= warning_threshold:
        exit_code = 1
    if hrStorageUsedPercent >= critical_threshold:
        exit_code = 2
    
    service_output(
        title = 'MEMORY',
        exit_code = exit_code,
        message = 'Used: {}/{}GB ({}%)'.format(round(hrStorageUsed * 10**-9,1), round(hrStorageSize * 10**-9,1), hrStorageUsedPercent),
        perfdata = '\'memory\'={}B;{};{};{};{}'.format(
            hrStorageUsed,
            round(warning_threshold*hrStorageSize/100),
            round(critical_threshold*hrStorageSize/100),
            0,
            hrStorageSize)
    )

###############################################################################################################

# CPU check
if args.command == 'cpu':
    
    prefix = 'iso.org.dod.internet.mgmt.mib-2.25.3.3.1.'

    hrProcessorFrwID_OID = prefix + '1'
    hrProcessorLoad_OID = prefix + '2'


    success, result, message = snmp_util.snmp_table(
        host = args.host,
        oids = [
            hrProcessorFrwID_OID,
            hrProcessorLoad_OID,
        ],
        version = args.snmp_version,
        community = args.snmp_community
    )

    if not success :
        service_output(
            title = 'CPU',
            exit_code = 3,
            message = message
        )

    warning_threshold = (args.warning if args.warning != None else 90)
    critical_threshold = (args.critical if args.critical != None else 100)
  
    avg_load=0
    perfdata  = ''
    index=0
    for cpu in result:
        avg_load += int(cpu[hrProcessorLoad_OID])
        perfdata += '\'cpu{}\'={}%;{};{};{};{};'.format(
            index,
            cpu[hrProcessorLoad_OID],
            '',
            '',
            0,
            100)
        index += 1
    avg_load = avg_load/len(result)

    perfdata  = '\'avg\'={}%;{};{};{};{};'.format(
            int(avg_load),
            round(warning_threshold),
            round(critical_threshold),
            0,
            100) + perfdata



    exit_code = 0
    if avg_load >= warning_threshold:
        exit_code = 1
    if avg_load >= critical_threshold:
        exit_code = 2
    
    service_output(
        title = 'CPU',
        exit_code = exit_code,
        message = 'Load: {}% ({} CPUs)'.format(int(avg_load), len(result)),
        perfdata = perfdata
    )

###############################################################################################################

# Uptime check
if args.command == 'uptime':
    
    hrSystemUptime_OID = 'iso.org.dod.internet.mgmt.mib-2.25.1.1.0'

    success, result, message = snmp_util.snmp_get(
        host = args.host,
        oids = [
            hrSystemUptime_OID,
        ],
        version = args.snmp_version,
        community = args.snmp_community
    )

    if not success :
        service_output(
            title = 'UPTIME',
            exit_code = 3,
            message = message
        )

    hrProcessorFrwID_index = 0
    hrProcessorLoad_index = 1
    
    hrSystemUptime_ticks = int(result[hrSystemUptime_OID])
    hrSystemUptime_datetime = datetime.timedelta(seconds = hrSystemUptime_ticks/100)

    hrSystemUptime_days = hrSystemUptime_datetime.days
    hrSystemUptime_hours = math.ceil(hrSystemUptime_datetime.seconds/3600)
    hrSystemUptime_minutes = math.ceil((hrSystemUptime_datetime.seconds%3600)/60)

    warning_threshold = (args.warning if args.warning != None else 183)
    critical_threshold = (args.critical if args.critical != None else 365)

    exit_code = 0
    if hrSystemUptime_days >= warning_threshold:
        exit_code = 1
    if hrSystemUptime_days >= critical_threshold:
        exit_code = 2
    
    service_output(
        title = 'UPTIME',
        exit_code = exit_code,
        message = 'Uptime: {} days {} hours {} minutes'.format(hrSystemUptime_days, hrSystemUptime_hours, hrSystemUptime_minutes),
        perfdata = '\'uptime\'={}days;{};{};{};{};'.format(
            hrSystemUptime_days,
            warning_threshold,
            critical_threshold,
            0,
            400)
    )

###############################################################################################################

# Logging level check
if args.command == 'logging':
    if args.mics_password == '' :
        service_output(
            title = 'LOGGING',
            exit_code = 3,
            message = 'MICS password required'
        )
    
    success, result = mics_util.mics_info(
        host= args.host,
        username = args.mics_username,
        password = args.mics_password,
        method = 'POST',
        uri = '/mics/mics.html',
        data = {
            'action': 'getLogs',
            'productType': 'Senry',
            'command': 'getLogs'
        },
        port= 8443
    )

    if not success :
        service_output(
            title = 'LOGGING',
            exit_code = 3,
            message = result
        )
   
    warning_threshold = (args.warning if args.warning != None else 1)
    critical_threshold = (args.critical if args.critical != None else 3)


    json_res = json.loads(result)
    #log_level = json.loads(json_res['asproxy'])
    sentry_log_enabled = (True if re.search(r'"enable":"(\w+)"',json_res['asproxy']).group(1) == 'true' else False)
    log_level = int(re.search(r'"verbosity":"level([0-9])"',json_res['asproxy']).group(1))
 
    exit_code = 0
    if sentry_log_enabled :
        if log_level >= warning_threshold :
            exit_code = 1
        if log_level >= critical_threshold :
            exit_code = 2
    

    service_output(
        title = 'LOGGING',
        exit_code = exit_code,
        message = 'Sentry logging {} (level: {})'.format(('enabled' if sentry_log_enabled else 'disabled'), log_level),
        perfdata = '\'log_level\'={},{},{},{},{}'.format(
            log_level,
            warning_threshold,
            critical_threshold,
            0,
            4
            )
    )

###############################################################################################################

# DNS check
if args.command == 'dns':
    if args.mics_password == '' :
        service_output(
            title = 'DNS',
            exit_code = 3,
            message = 'MICS password required'
        )
    
    success, result = mics_util.mics_info(
        host= args.host,
        username = args.mics_username,
        password = args.mics_password,
        method = 'GET',
        uri = '/mics/mics.html?_dc=1585503472800&servicename=DNS&action=testDiagnosticService&command=testDiagnosticService',
        port= 8443
    )

    if not success :
        service_output(
            title = 'DNS',
            exit_code = 3,
            message = result
        )

    json_res = json.loads(result)

    exit_code = 0
    if json_res['results'][0]['status'] == 'Failed' :
        exit_code = 2
    
    service_output(
        title = 'DNS',
        exit_code = exit_code,
        message = json_res['results'][0]['message'].replace('&lt;br&gt;', '')[:-1],
    )

###############################################################################################################

# NTP check
if args.command == 'ntp':
    if args.mics_password == '' :
        service_output(
            title = 'NTP',
            exit_code = 3,
            message = 'MICS password required'
        )
    
    success, result = mics_util.mics_info(
        host= args.host,
        username = args.mics_username,
        password = args.mics_password,
        method = 'GET',
        uri = '/mics/mics.html?_dc=1585509986551&servicename=NTP&action=testDiagnosticService&command=testDiagnosticService',
        port= 8443
    )

    if not success :
        service_output(
            title = 'NTP',
            exit_code = 3,
            message = result
        )

    json_res = json.loads(result)

    exit_code = 0
    if json_res['results'][0]['status'] == 'Failed' :
        exit_code = 2
    
    service_output(
        title = 'NTP',
        exit_code = exit_code,
        message = json_res['results'][0]['message'].replace('&lt;br&gt;', ' ')[:-1],
    )
    

###############################################################################################################

# Connected devices
if args.command == 'devices':
    if args.mics_password == '' :
        service_output(
            title = 'DEVICES',
            exit_code = 3,
            message = 'MICS password required'
        )
    
    success, result = mics_util.mics_info(
        host= args.host,
        username = args.mics_username,
        password = args.mics_password,
        method = 'GET',
        uri = '/mics/mics.html?_dc=1585511343484&action=getSentryUtilization&command=getSentryUtilization',
        port= 8443
    )

    if not success :
        service_output(
            title = 'DEVICES',
            exit_code = 3,
            message = result
        )

    json_res = json.loads(result)

    connected_devices = int(re.search(r'Number of Connected Devices  : ([0-9]+)', json_res['utilization']).group(1))

    system_scale = re.search(r'SYSTEM_SCALE=(\w+)', json_res['systemScale']).group(1)

    SYSTEM_SCALE_MAXIMUM = {
        'Small'  : 2000,
        'Medium' : 8000,
        'Large'  : 20000
    }

    system_scale_percent = connected_devices/SYSTEM_SCALE_MAXIMUM[system_scale]*100


    warning_threshold = (args.warning if args.warning != None else 80)
    critical_threshold = (args.critical if args.critical != None else 100)
    
    exit_code = 0
    if system_scale_percent >= warning_threshold:
        exit_code = 1
    if system_scale_percent >= critical_threshold:
        exit_code = 2
    
    service_output(
        title = 'DEVICES',
        exit_code = exit_code,
        message = 'Number of Connected Devices  : {} ({})'.format(connected_devices, system_scale),
        perfdata = '\'devices\'={}devices;{};{};{};{};'.format(
            connected_devices,
            int(warning_threshold*SYSTEM_SCALE_MAXIMUM[system_scale]/100),
            int(critical_threshold*SYSTEM_SCALE_MAXIMUM[system_scale]/100),
            0,
            SYSTEM_SCALE_MAXIMUM[system_scale])
    )
