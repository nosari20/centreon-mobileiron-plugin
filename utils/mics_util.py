###############################################################################################################
# Language     :  Python (3.x)
# Filename     :  mics_util.py
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
import ssl
import urllib3
import re

urllib3.disable_warnings()

#
# Check Core status
# host:  host FQDN or IP
# username: MICS username
# password: MICS password
# port: service port
#
# return success (if success 1 else 0) output
#
#
def mics_info(host: str, username:str, password:str, uri:str, method:str = 'GET', data:dict = {}, port: int = 8443) -> (bool, str) :
    
    # Sanitize input
    if uri.startswith('/') :
        uri = uri[1:]

    if method not in ['GET', 'POST'] :
        return False, 'Method \'{}\' not supported'.format(method)
    

    try:

        # Login most data
        post_data = {
            'j_username' : username,
            'j_password' : password
        }

        # Login additional headers
        headers = {
            'referer' : 'https://{}:{}/mics/login.jsp'.format(host,port)
        }

        # Create session
        session = requests.Session() 

        # Perform login
        r = session.post(
            'https://{}:{}/mics/j_spring_security_check'.format(host,port),
            headers = headers, 
            data = post_data,
            verify=False
        )

        # If http 200 check data
        if r.status_code == 200:

            content = r.text
            # Check if succesfull login
            if 'Login Failed' in content :
                return False, 'LOGIN: Login Failed. Invalid username or password. Multiple invalid attempts may result in account lockout.'
            else :

                # Retrieve session and csrf info
                csrfKey = re.search(r'csrfKey = \"(\w+)\";', content).group(1)
                csrfNonce = re.search(r'csrfNonce = \"(\w+)\";', content).group(1)

                # Set additional cookies
                session.cookies.set('_mi_isLoggedIn', '1')

                # Request additional headers
                headers = {
                    'authUserId' : username,
                    'Origin' : 'https://{}:{}'.format(host,port),
                    'referer' : 'https://{}:{}/mics/mics.html'.format(host,port),
                    'X-Requested-With' : 'XMLHttpRequest',
                    csrfKey : csrfNonce
                }

                if method == 'POST' :
                    r = session.post(
                        #'https://{}:{}/mics/mics.html?_dc=1585491075918&servicename=DNS&action=testDiagnosticService&command=testDiagnosticService'.format(host,port),
                        'https://{}:{}/{}'.format(host,port,uri),
                        headers = headers, 
                        verify=False,
                        data = data,
                    )
                else :
                    r = session.request(
                        method,
                        #'https://{}:{}/mics/mics.html?_dc=1585491075918&servicename=DNS&action=testDiagnosticService&command=testDiagnosticService'.format(host,port),
                        'https://{}:{}/{}'.format(host,port,uri),
                        headers = headers, 
                        verify=False
                    )

                if r.status_code == 200:
                    return True, r.text
                else:
                    return False, 'REQUEST: HTTP ' + str(r.status_code)
                print(r.text)

            

        else:
            return False, 'LOGIN: HTTP ' + str(r.status_code)


    # Handle HTTP errors
    except requests.exceptions.HTTPError as e:
        return False, e.response.text

    # Handle others errors
    except BaseException as err:
        return False, format(err)
###############################################################################################################