###############################################################################################################
# Language     :  Python (3.x)
# Filename     :  status_util.py
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

import requests
import urllib3

urllib3.disable_warnings()

#
# Check Core status
# host:  host FQDN or IP
# port: service port
#
# return success (if success 1 else 0) status (0 if KO, 1 if issue, 2 if KO), error
#
#
def core_status(host: str, port: int = 443) -> (bool, int, str) :
 
    # Perform status page request
    try:
        r = requests.get('https://'+host+'/status/status.html', verify=False)

        # if http 200 check data
        if r.status_code == 200:
            
            if 'MOBILEIRON-STATUS: OK' in r.text:
                # Core status OK
                return True, 2, 'Core OK'
            else:
                # Core status KO
                return True, 0, 'Core KO'

        else:
            return False, None, 'HTTP ' + r.status_code


    # Handle HTTP errors
    except requests.exceptions.HTTPError as e:
        return False, None, e.response.text

    # Handle others errors
    except BaseException as err:
        return False, None, format(err)

#
# Check Connector(s) status
# host:  host FQDN or IP
# port: service port
#
# return exit_code, message
#  
def connector_status(host: str, port: int = 443) -> (bool, int, str) :
 
    # Perform status page request
    try:
        r = requests.get('https://'+host+'/status/status.html', verify=False)

        # if http 200 check data
        if r.status_code == 200:
            
            # Count all setup connectors
            connectors = [line for line in r.text.split('\n') if 'theConnectorNameString' in line]
            connectors_up = len(connectors)

            connectors_OK = []
            connectors_KO = []

            # check each connectors status if used
            if connectors_up > 0 :
                for connector in connectors:
                    connector_name = connector.replace('theConnectorNameString=','').split(';')[0]
                    if 'isHealthytrue' not in connector:
                        # Connector status K0
                        connectors_KO.append(connector_name)
                    else:   
                        # Connector status OK
                        connectors_OK.append(connector_name)

                if len(connectors_OK) == 0 :
                    return True, 0, 'DOWN: {}'.format(str(connectors_KO))

                if len(connectors_OK) > 0 & len(connectors_KO) > 0:
                    return True, 1, 'UP: {}, DOWN: {}'.format(str(connectors_OK),str(connectors_KO))
                
                return True, 2, 'UP: {}'.format(str(connectors_OK))

            else:
                # No connector setup
                return False, None, 'No connector found'

        else:
            return False, None, 'HTTP ' + str(r.status_code)


    # Handle HTTP errors
    except requests.exceptions.HTTPError as e:
        return False, None, e.response.text

    # Handle others errors
    except BaseException as err:
        return False, None, format(err)
###############################################################################################################