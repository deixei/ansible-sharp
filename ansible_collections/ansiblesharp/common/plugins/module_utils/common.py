#!/usr/bin/python
#
# Copyright (c) 2024 Marcio Parente

import time
import base64

def normalize_location_name(name):
    return name.replace(' ', '').lower()

def get_timestamp() -> str:
    return str(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time())))

def format_message(err, resp):
    '''Example: msg = format_message("Failed to create temporary content file: %s" % to_native(e), resp)'''
    msg = resp.pop('msg')
    return err + (' %s' % msg if msg else '')

def basic_authorization(username, password):
    credentials = f"{username}:{password}"
    b = base64.b64encode(bytes(credentials, 'utf-8')) # bytes
    encoded_credentials = b.decode('utf-8') # convert bytes to string
    
    return "Basic " + encoded_credentials

class MonitoringAttributes():
    INSTRUMENTATION_KEY = "976c1cfe-d829-40af-b9da-c68670c14099"
    INSTRUMENTATION_KEY_CONNECTION_STRING = "InstrumentationKey=976c1cfe-d829-40af-b9da-c68670c14099;IngestionEndpoint=https://westeurope-5.in.applicationinsights.azure.com/;LiveEndpoint=https://westeurope.livediagnostics.monitor.azure.com/"
    
