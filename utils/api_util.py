###############################################################################################################
# Language     :  Python (3.x)
# Filename     :  api_util.py
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
import json
from typing import Any


urllib3.disable_warnings()

#
# Check Core status
# host:  host FQDN or IP
# port: service port
# filter: filter
# return success (if success 1 else 0) response (json response or error message)
#
#
def core_api(host: str, request: str, username: str, password: str, port: int = 443) -> (bool, Any) :
 
    # Sanitize request
    if not request.startswith('/') :
        request = '/' + request

    # Perform request
    try:
        r = requests.get('https://'+host+'/api/v2{}'.format(request), verify=False, auth=(username, password))

        # if http 200 check data
        if r.status_code == 200:

            return True, r.text

        else:
            return False, 'HTTP ' + str(r.status_code)


    # Handle HTTP errors
    except requests.exceptions.HTTPError as e:
        return False, None, e.response.text

    # Handle others errors
    except BaseException as err:
        return False, format(err)
###############################################################################################################