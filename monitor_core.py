#!/usr/bin/python3

###############################################################################################################
# Language     :  Python (3.7)
# Filename     :  monitore_core.py
# Autor        :  https://github.com/nosari20
# Description  :  Nagios/Centreon plugin for MobileIron Core
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
from utils import status_util, cert_util, snmp_util, tcp_util, mics_util


# Command line parser setup
usage = '%(prog)s <host> <command> [options]'
description = 'Nagios/Centreon plugin for MobileIron Core'
parser = argparse.ArgumentParser(description=description, usage=usage)


# Args
parser.add_argument('host',
                    metavar='host', 
                    type=str,
                    help='Host FQDN of IP')

parser.add_argument('command',
                    metavar='command', 
                    type=str,
                    choices=['tcp_ping', 'status', 'certificate', 'storage', 'memory', 'cpu', 'uptime', 'logging', 'dns', 'ntp'],
                    help='Available commands: tcp_ping,status, certificate, storage, memory, cpu, uptime, logging, dns, ntp')


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

group_tcp.add_argument('--tcp-port',
                    dest='tcp_port',
                    type=int,  
                    default=443,
                    help='Port (default: 443)')

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

# Core/Connector status
group_status = parser.add_argument_group('Options for status check')

group_status.add_argument('--status-component',
                    dest='status_component',
                    type=str,  
                    default='core',
                    choices=['core', 'connector'],
                    help='Component (default: \'core\')')


# Certificates
group_status = parser.add_argument_group('Options for certificate check')

group_status.add_argument('--certificate',
                    dest='certificate',
                    type=str,  
                    default='portal_https',
                    choices=['portal_https', 'client_tls'],
                    help='Certificate (default: \'portal_https\')')

# SNMP
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
        port = args.tcp_port,
        timeout = 1,
        packets = args.tcp_attempt
    )
    

    if not success :
        service_output(
        title = 'TCP PORT {}'.format(args.tcp_port),
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
        title = 'TCP PORT {}'.format(args.tcp_port),
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

# Status check
if args.command == 'status':
    if args.status_component == 'core' :
        success, status, message = status_util.core_status(
            host = args.host,
            port = 443
        )
    elif args.status_component == 'connector' :
        success, status, message = status_util.connector_status(
            host = args.host,
            port = 443
        )

    if not success :
        service_output(
        title = '{} STATUS'.format(args.status_component.upper()),
        exit_code = 3, 
        message = message
    )

    exit_code = 0
    if status == 0 :
        exit_code = 2
    if status == 1 :
        exit_code = 1

    service_output('{} STATUS'.format(args.status_component.upper()), exit_code, message)

###############################################################################################################

# SSL check
if args.command == 'certificate':
    if args.certificate == 'portal_https' :
        success, remaining_days, message = cert_util.check_cert(
            host = args.host,
            port = 443
        )
    elif args.certificate == 'client_tls' :
        success, remaining_days, message = cert_util.check_cert(
            host = args.host,
            port = 9997
        )

    if not success :
        service_output(
        title = 'CERTIFICATE \'{}\''.format(args.certificate.replace('_', ' ').upper()),
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
        title = 'CERTIFICATE \'{}\''.format(args.certificate.replace('_', ' ').upper()),
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
    index = 0
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
            'productType': 'VSP',
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
   
    warning_threshold = (args.warning if args.warning != None else 2)
    critical_threshold = (args.critical if args.critical != None else 4)


    json_res = json.loads(result)
    log_level_list = json_res['logLevelsForPackages']
    mifs_log_enabled = (True if json_res['mifs'] == 'enable' else False)

    LOG_LEVEL_INT = {

        'OFF'   : 0,
        'ERROR' : 1,
        'WARN'  : 2,
        'INFO' : 3,
        'DEBUG' : 4,
        'TRACE' : 5,
    }

    exit_code = 0
    
    perfdata = ''
    for package in log_level_list :
        if package != 'EnablePackages' :
            log_level = 0
            if mifs_log_enabled : 
                log_level = LOG_LEVEL_INT[log_level_list[package]]

            
            if log_level >= warning_threshold and exit_code < 1 :
                exit_code = 1
            if log_level >= critical_threshold :
                exit_code = 2
            

            perfdata += '\'{}\'={};{};{};{};{};'.format(
                package,
                log_level,
                warning_threshold,
                critical_threshold,
                0,
                5)
            

    perfdata += '\'{}\'={};{};{};{};{};'.format(
                package,
                LOG_LEVEL_INT[log_level_list[package]],
                warning_threshold,
                critical_threshold,
                0,
                5)
    

    service_output(
        title = 'LOGGING',
        exit_code = exit_code,
        message = ('MIFS logging enabled' if mifs_log_enabled else 'MIFS logging enabled'),
        perfdata = perfdata
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
    


