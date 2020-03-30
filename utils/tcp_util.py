###############################################################################################################
# Language     :  Python (3.7)
# Filename     :  tcp_util.py
# Autor        :  https://github.com/nosari20
# Description  :  Nagios/Centreon plugin for MobileIron Core
# Repository   :  https://github.com/nosari20/centreon-mobileiron-plugin
###############################################################################################################
#
### Changelog ###
#
# ~~ Version 0.1 ~~
#
#
#################

import sys
import socket
import time
from timeit import default_timer as timer

#
# TCP pin 
# host:  host FQDN
# port: service port
# verbose: allow printing
#
# return success (if success 1 else 0) time passed  failed error
#
def tcp_ping(host: str, port: int, timeout: int = 1, packets: int = 20) -> (bool, float, int, int, str) :

    def connect(host: str, port: int, timeout: int) -> (bool, int) :

        # Setup socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)     
       
        try:
            
            # Get t0 time
            t0 = timer()

            # Start connection
            s.connect((host, int(port)))

            # Close connection
            s.shutdown(socket.SHUT_RD)

            # Get t1 time
            t1 = timer()

            return True, (t1-t0)*1000
        
        # Timed Out
        except socket.timeout:

            return False, -1
            

    try :

        passed = 0
        avg_time = 0

        # Perform connection test
        for x in range(packets) :
            success, time = connect(host, port, timeout)
            if success :
                avg_time += time
                passed += 1

        if passed > 0 :
            avg_time = avg_time / passed 
        else :
            avg_time = -1

        return True, avg_time, passed, packets - passed, ''

    except BaseException as err:
        return False, -1, -1, -1, format(err)


    


