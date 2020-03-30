# Centreon plugin for MobileIron

[![Version](https://img.shields.io/badge/Version-1.0-red.svg)](https://shields.io/) [![made-with-python](https://img.shields.io/badge/Made%20with-Python%203.7-1f425f)](https://www.python.org/) [![Ask Me Anything !](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](https://github.com/nosari20/centreon-mobileiron-plugin/issues)

## Supported appliances/services

* Core
    * TCP ping
    * Core and Connector status (via status page)
    * Certificates (Portal HTTPS and Client TLS)
    * SNMP
        * Storage
        * Memory
        * CPU load
        * Uptime
    * MICS
        * Logging level
        * DNS
        * NTP

* Sentry
    * TCP ping
    * Core and Connector status (via status page)
    * Certificates (Portal HTTPS and Client TLS)
    * SNMP
        * Storage
        * Memory
        * CPU load
        * Uptime
    * MICS
        * Logging level
        * DNS
        * NTP
        * Connected devices

## TODO

* Device list count with filters (via API)
* Device compliance
* Connector monitoring
* Cloud suport
* HA check (via ha status page)
* [Submit an idea](https://github.com/nosari20/centreon-mobileiron-plugin/issues)



## Installation
```bash
$ git clone https://github.com/nosari20/centreon-mobileiron-plugin
```

## Usage

### Core


#### TCP ping

|  Return Code  |             Time                  |     Failed percentage             |     Status    |
|---------------|-----------------------------------|-----------------------------------|---------------|  
|      0        |              OK                   |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |  TCP FAILED WARNING THRESHOLD     |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |  TCP FAILED CRITICAL THRESHOLD    |     CRITICAL  |
|      3        |            UNKNOWN                |             UNKNOWN               |     UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.com tcp_ping [--tcp-port 443] [--tcp-attempt 20] [--warning 1000] [--critical 2000] [tcp-failed-warning 50] [tcp-failed-critical 100]

TCP PORT 443 OK - time=132ms passed=20 failed=0;|'time'=132ms;1000;2000;0;3000;'failed'=0%;50;100;0;100;
```

#### Core/Connector status (no SSL check)

|  Return Code  |     Core Status       |       Connecort Status        |       Status      | 
|---------------|-----------------------|-------------------------------|-------------------|    
|      0        |         OK	        |          ALL OK               |         OK	    |
|      1        |         KO            |     1 OR MORE REMAINING	    |       WARNING	    |
|      2        |         KO	        |          ALL KO	            |       CRITICAL    |	
|      3        |      UNKNOWN	        |         UNKNOWN	            |       UNKNOWN	    |


Core status
```bash
$ ./monitor_core.py micore.example.com status

CORE STATUS OK - Core OK
```

Connector status
```bash
$ ./monitor_core.py micore.example.com --status-component connector

CONNECTOR STATUS OK - UP: ['CONNECTOR_01', 'CONNECTOR_02']
```

#### Certificate Portal HTTPS and Client TLS

|  Return Code  |           Certificate             |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |               OK                  |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |   SSL ERROR OR CRITICAL THRESHOLD |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |

Portal HTTPS
```bash
$ ./monitor_core.py micore.example.com certificate [--certificate portal_https] [--warning 60] [--critical 30]

CERTIFICATE 'PORTAL HTTPS' OK - Days remaining before expiration: 218
```

Client TLS
```bash
$ ./monitor_core.py micore.example.com certificate --certificate client_tls [--warning 60] [--critical 30]

CERTIFICATE 'CLIENT TLS' OK - Days remaining before expiration: 218
```

#### Storage (via SNMP)

|  Return Code  |            Storage                |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra storage [--snmp-community public] [--snmp-version 1] [--warning 70] [--critical 90]

STORAGE OK - Used: 9.3/79.3GB (11.7%);|'/'=162611200B;716312576;920973312;0;1023303680;'/dev/shm'=28672B;;;0;1973645312,'/run'=20340736B;;;0;1973645312,'/sys/fs/cgroup'=0B;;;0;1973645312,'/boot'=162611200B;;;0;1023303680,
```




#### Memory (via SNMP)

|  Return Code  |            Memory                 |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra memory [--snmp-community public] [--snmp-version 1] [--warning 90] [--critical 100]

MEMORY WARNING - Used: 3.8/3.9GB (95.8%);|'memory'=3783036928B;3552561561;3947290624;0;3947290624
```

#### CPU (via SNMP)

|  Return Code  |              CPU                  |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra cpu [--snmp-community public] [--snmp-version 1] [--warning 90] [--critical 100]

CPU OK - Load: 1% (2 CPUs);|'avg'=0%;90;100;0;100;'cpu0'=1%;;;0;100'cpu1'=1%;;;0;100
```

#### Uptime (via SNMP)

|  Return Code  |            Uptime                 |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra uptime [--snmp-community public] [--snmp-version 1] [--warning 183] [--critical 365]

UPTIME OK - Uptime: 7 days 5 hours 13 minutes;|'uptime'=7days;183;365;0;400;
```

#### Loggin (via MICS)

|  Return Code  |         Loging level              |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra logging [--mics-password admin] [--mics-password <PASS>] [--warning 2] [--critical 4]

LOGGING OK - MIFS logging enabled;|'All'=0;2;4;0;5;'Policies'=0;2;4;0;5;'LDAP'=0;2;4;0;5;'ClientCheckIn'=0;2;4;0;5;'Windows'=0;2;4;0;5;'Security'=0;2;4;0;5;'IOS'=0;2;4;0;5;'Controller'=0;2;4;0;5;'Statistics'=0;2;4;0;5;'AppStore'=0;2;4;0;5;'DEP'=0;2;4;0;5;'Notification'=0;2;4;0;5;'AppConnect'=0;2;4;0;5;'Android'=0;2;4;0;5;'Rest'=0;2;4;0;5;'DAO'=0;2;4;0;5;'Gateway'=0;2;4;0;5;'Registration'=0;2;4;0;5;'VPP'=0;2;4;0;5;'DeviceSpace'=0;2;4;0;5;'SCEP'=0;2;4;0;5;'Certificate'=0;2;4;0;5;'Certificate'=3;2;4;0;5;
```

#### DNS (via MICS)

|  Return Code  |         DNS     |
|---------------|-----------------|
|      0        |         OK      |
|      1        |         -       |
|      2        |         KO      |
|      3        |       UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra dns [--mics-password admin] [--mics-password <PASS>]

DNS CRITICAL - DNS server 8.8.8.8 is reachable.DNS server 4.4.4.1 is not reachable;
```

#### NTP (via MICS)

|  Return Code  |         DNS     |
|---------------|-----------------|
|      0        |         OK      |
|      1        |         -       |
|      2        |         KO      |
|      3        |       UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra ntp [--mics-password admin] [--mics-password <PASS>]

NTP OK - NTP server 192.168.1.24 is reachable.;
```



### Sentry

#### TCP ping

|  Return Code  |             Time                  |     Failed percentage             |     Status    |
|---------------|-----------------------------------|-----------------------------------|---------------|  
|      0        |              OK                   |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |  TCP FAILED WARNING THRESHOLD     |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |  TCP FAILED CRITICAL THRESHOLD    |     CRITICAL  |
|      3        |            UNKNOWN                |             UNKNOWN               |     UNKNOWN   |


```bash
$ ./monitor_sentry.py misentry.example.com tcp_ping [--tcp-port 443] [--tcp-attempt 20] [--warning 1000] [--critical 2000] [tcp-failed-warning 50] [tcp-failed-critical 100]

TCP PORT 443 OK - time=132ms passed=20 failed=0;|'time'=132ms;1000;2000;0;3000;'failed'=0%;50;100;0;100;
```


#### Certificate

|  Return Code  |           Certificate             |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |               OK                  |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |   SSL ERROR OR CRITICAL THRESHOLD |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_sentry.py misentry.example.com certificate [--sentry-port 443] [--warning 60] [--critical 30]

CERTIFICATE PORT 443 OK - Days remaining before expiration: 712;
```

#### Storage (via SNMP)

|  Return Code  |            Storage                |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_sentry.py misentry.example.intra storage [--snmp-community public] [--snmp-version 1] [--warning 70] [--critical 90]

STORAGE OK - Used: 9.3/79.3GB (11.7%);|'/'=162611200B;716312576;920973312;0;1023303680;'/dev/shm'=28672B;;;0;1973645312,'/run'=20340736B;;;0;1973645312,'/sys/fs/cgroup'=0B;;;0;1973645312,'/boot'=162611200B;;;0;1023303680,
```

#### Memory (via SNMP)

|  Return Code  |            Memory                 |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_sentry.py misentry.example.intra memory [--snmp-community public] [--snmp-version 1] [--warning 90] [--critical 100]

MEMORY WARNING - Used: 3.8/3.9GB (95.8%);|'memory'=3783036928B;3552561561;3947290624;0;3947290624
```

#### CPU (via SNMP)

|  Return Code  |              CPU                  |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_sentry.py misentry.example.intra cpu [--snmp-community public] [--snmp-version 1] [--warning 90] [--critical 100]

CPU OK - Load: 1% (2 CPUs);|'avg'=0%;90;100;0;100;'cpu0'=1%;;;0;100'cpu1'=1%;;;0;100
```

#### Uptime (via SNMP)

|  Return Code  |            Uptime                 |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_sentry.py misentry.example.intra uptime [--snmp-community public] [--snmp-version 1] [--warning 183] [--critical 365]

UPTIME OK - Uptime: 7 days 5 hours 13 minutes;|'uptime'=7days;183;365;0;400;
```

#### Logging (via MICS)

|  Return Code  |         Loging level              |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_sentry.py misentry.example.intra logging [--mics-password admin] [--mics-password <PASS>] [--warning 1] [--critical 3]

LOGGING OK - Sentry logging disabled (level: 3);|'log_level'=3,1,4,0,4
```

#### DNS (via MICS)

|  Return Code  |         DNS     |
|---------------|-----------------|
|      0        |         OK      |
|      1        |         -       |
|      2        |         KO      |
|      3        |       UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra dns [--mics-password admin] [--mics-password <PASS>]

DNS CRITICAL - DNS server 8.8.8.8 is reachable.DNS server 4.4.4.1 is not reachable;
```

#### NTP (via MICS)

|  Return Code  |         DNS     |
|---------------|-----------------|
|      0        |         OK      |
|      1        |         -       |
|      2        |         KO      |
|      3        |       UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra ntp [--mics-password admin] [--mics-password <PASS>]

NTP OK - NTP server 192.168.1.24 is reachable.;
```

#### Conected devices (via MICS)

|  Return Code  |  Number of connected devices      |     Status    |
|---------------|-----------------------------------|---------------|  
|      0        |              OK                   |       OK	    |
|      1        |           WARNING THRESHOLD       |     WARNING   |
|      2        |           CRITICAL THRESHOLD      |     CRITICAL  |
|      3        |            UNKNOWN                |     UNKNOWN   |


```bash
$ ./monitor_core.py micore.example.intra ntp [--mics-password admin] [--mics-password <PASS>] [--warning 80] [--critical 100]

DEVICES OK - Number of Connected Devices  : 0 (Small);|'devices'=0devices;1600;2000;0;2000;
```

## Notes 

### SNMP versions

|     Code      |       SNMP Version     |
|---------------|------------------------|  
|      0        |           v1           |
|      1        |           v2c          |
