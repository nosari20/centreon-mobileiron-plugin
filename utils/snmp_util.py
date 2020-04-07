###############################################################################################################
# Language     :  Python (3.x)
# Filename     :  check_snmp.py
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

from pysnmp.hlapi import *

#
# SNMP get 
# host:  host FQDN
# oids: list of OIDs
# version: SNMP version (0:v1, 1:v2)
# community: SNMP community
# return success (if success 1 else 0) result (oid=>value) message
#
def snmp_get(host: str, oids: [str], version: int = 1, community: str = 'public',) -> (bool, dict, str):

    query = ()
    for oid in oids:
        query = query + (ObjectType(ObjectIdentity(oid)),)

    try :

        
        # Init SNMP request
        SNMP_ENGINE = SnmpEngine()
        SNMP_COMMUNITY = CommunityData(community, mpModel=version)
        SNMP_TRANSPORT = UdpTransportTarget((host, 161))
        SNMP_CONTEXT = ContextData()

        
        # Create get query
        g = getCmd(SNMP_ENGINE,SNMP_COMMUNITY, SNMP_TRANSPORT, SNMP_CONTEXT, *query)

        # Execute query
        errorIndication, errorStatus, errorIndex, varBinds = next(g)
            
        # Error handler
        if errorIndication:
            return False, None, str(errorIndication)
            
        if errorStatus:
            return False, None, errorStatus.prettyPrint()

        else:
            result = {}

            for index, value in enumerate(varBinds) :
                result[oids[index]] = str(value[1])

            return True, result, None

    except BaseException as err:  
        return False, None, format(err)
    
    

def snmp_table(host: str, oids: [str], version: int = 1, community: str = 'public',) -> (bool, dict, str):
    query = ()
    for oid in oids:
        query = query + (ObjectType(ObjectIdentity(oid)),)

    try :

        
        # Init SNMP request
        SNMP_ENGINE = SnmpEngine()
        SNMP_COMMUNITY = CommunityData(community, mpModel=version)
        SNMP_TRANSPORT = UdpTransportTarget((host, 161))
        SNMP_CONTEXT = ContextData()

        
        # Create and execute execute next query
        g = nextCmd(SNMP_ENGINE,SNMP_COMMUNITY, SNMP_TRANSPORT, SNMP_CONTEXT, lexicographicMode=False, *query)

        # Create table result
        table = []
        dim = len(oids)
        index = 0
        row = dict()
        for (errorIndication, errorStatus, errorIndex, varBinds) in g :  
        
            # Error handler
            if errorIndication:
                return False, None, str(errorIndication)
                
            if errorStatus:
                return False, None, errorStatus.prettyPrint()

            else:
                for varBind in varBinds :
                    row[oids[index]] = str(varBind[1])
                    if index  == len(oids) - 1 :
                        table.append(row)
                        row = dict()
                        index = 0
                    else :
                        index += 1

        return True, table, None

    except BaseException as err:  
        return False, None, format(err)
###############################################################################################################