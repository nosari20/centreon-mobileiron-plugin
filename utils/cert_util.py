###############################################################################################################
# Language     :  Python (3.7)
# Filename     :  cert_util.py
# Autor        :  https://github.com/nosari20
# Description  :  Nagios/Centreon plugin for MobileIron Core
# Repository   :  https://github.com/nosari20/centreon-mobileiron-plugin
#
### Changelog ###
#
# ~~ Version 0.1 ~~
#
#
#################

import socket
import ssl
import json
from datetime import datetime, timedelta
import traceback

# Workaround for OSError during Sentry certificate check
import os
from cryptography import x509
from cryptography.hazmat.backends import default_backend
#
# Check certificate 
# host:  host FQDN
# port: service port
# verbose: allow printing
#
# return success (if success 1 else 0) remaining_days message
#
def check_cert(host: str, port: int) -> (bool, int, str) :

    try:
        # Perform certificate validation
        context = ssl.create_default_context()
        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                # SSL OK
                # Check if the certificate will expire in less than 'warning_threshold' or 'critical_threshold' days
                cert = ssock.getpeercert()
                ssl_date_fmt = '%b %d %H:%M:%S %Y %Z'
                current = datetime.now()
                notAfter = datetime.strptime(cert['notAfter'], ssl_date_fmt)
                notBefore = datetime.strptime(cert['notBefore'], ssl_date_fmt)
                remainingDays = abs((current - notAfter).days)
  
                return True, remainingDays, 'Days remaining before expiration: {}'.format(remainingDays)
               


    # Handle SSL errors
    except ssl.SSLError as sslErr:
        return True, 0, 'SSL: ' + str(sslErr.reason)


    # Workaround for OSError during Sentry certificate check
    except OSError :
        RAW_OPENSSL_COMMAND='openssl s_client -connect {}:{} 2>/dev/null </dev/null |  sed -ne \'/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p\''.format(host,port)
        command = os.popen(RAW_OPENSSL_COMMAND)
        cert_str = command.read()
        cert = x509.load_pem_x509_certificate(bytes(cert_str,'utf8'), default_backend())

        ssl_date_fmt = '%b %d %H:%M:%S %Y %Z'
        current = datetime.now()
        notAfter = cert.not_valid_after
        notBefore = cert.not_valid_before
        remainingDays = abs((current - notAfter).days)
  
        return True, remainingDays, 'Days remaining before expiration: {}'.format(remainingDays)

    # Handle others errors
    except BaseException as err:
        return False, 0, format(err)
###############################################################################################################

