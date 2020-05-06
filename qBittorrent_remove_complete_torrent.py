#!/usr/bin/python3
import sys
import json
import requests
import logging
import argparse
import os
from requests import Request
import requests
from requests import Session
from requests.exceptions import RequestException

########## CONFIGURATIONS ##########
# Access Information for qBittorrent
qBittorrent_username='admin'
qBittorrent_password='adminadmin'
# Host on which qBittorrent runs
qBittorrent_host='http://localhost'
# Port
qBittorrent_port=8081
########## CONFIGURATIONS ##########

# Set up logging - kinda important when deleting stuff!
thisFile = os.path.basename(__file__)#.split('.')[0]
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")
rootLogger = logging.getLogger()
LogTo = '/tmp/'+thisFile.split('.')[0]+'.log'
fileHandler = logging.FileHandler(LogTo)
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
rootLogger.setLevel(logging.INFO)
debugmode = 0
testmode = 0
OlderApi = 0

host = str(qBittorrent_host) + ':' + str(qBittorrent_port)

def HowTo():
    print('')
    print(thisFile+' [option]', end='\n * ')
    print('Clears "Completed" status torrents from qBitTorrent', end='\n * ')
    print('Connects to "localhost:8080" without credentials', end='\n * ')
    print('Logs output to '+LogTo, end='\n * ')
    print('By default logs nothing to stdout/stderr to allow use in cron')
    print('')
    print('Options:', end='\n   ')
    print('-v --verbose : to enable console logging in addition to logfile', end='\n   ')
    print('-t --test    : for test mode (no delete) - implies -v')
    print('')
    exit(0)

def qBittorrentApiCheck():
    s = requests.Session()

    api_url = host + "/api/v2/app/webapiVersion"

    if s.get(api_url).status_code == 200: # API v2.4.1
        print('Api version: ' + s.get(api_url).text)
        print('Setting up variables ...')
        Api_Get_Torrents = '/api/v2/torrents/info?filter=completed'
        return Api_Get_Torrents
    else:
        api_url = host + "/version/api"
        if s.get(api_url).status_code == 200: # Older API
            print('Api version: ' + s.get(api_url).text)
            print('Setting up variables ...')
            Api_Get_Torrents = '/query/torrents?filter=completed'
            OlderApi = 1
            return Api_Get_Torrents
        else:
            print('I can\' find the api version, I\'ll quit')
            exit(0)

    print()
    print('OK lets do stuff')

if len(sys.argv) > 1 and ( str(sys.argv[1]) == '-v' or str(sys.argv[1]) == '--verbose' ):
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    rootLogger.setLevel(logging.DEBUG)
    debugmode = 1

if len(sys.argv) > 1 and ( str(sys.argv[1]) == '-t' or str(sys.argv[1]) == '--test' ):
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    rootLogger.setLevel(logging.DEBUG)
    debugmode = 1
    testmode = 1

if len(sys.argv) > 1 and ( str(sys.argv[1]) == '-?' or str(sys.argv[1]) == '--help' ):
    HowTo()

if len(sys.argv) > 1 and ( debugmode == 0 ):
    print(thisFile+': Invalid option "'+str(sys.argv[1])+'"')
    HowTo()

if len(sys.argv) > 2:
    print(thisFile+': Invalid option "'+str(sys.argv[2])+'"')
    HowTo()

#qBittorrentApiCheck()

# OK lets do stuff
exitcode = 0
try:
    #response = requests.get(host+Api_Get_Torrents)
    response = requests.get(host+qBittorrentApiCheck())
    response.raise_for_status()
    data = response.json()
    # Observed status for torrents in 'completed' filter:
    #  uploading - seeding
    #  stalledUP - seeding but stalled
    # >pausedUP  - seeding and manually paused
    #            - seeding and ratio reached but seeding time still to go

    if len(data) == 0:
        logging.debug('No completed torrents to clear')
        if debugmode == 1:
            print('')
        exit(0)
    for tor in data:
        # if tor['category'] != 'Film' and tor['category'] != 'Serie_Tv':
        #     logging.debug('Skipping '+tor['category']+' torrent: '+tor['name'])
        #     continue
        if tor['state'] != 'pausedUP':
            logging.debug('Skipping '+tor['state']+' torrent: '+tor['name'])
            continue

        logging.info('Clearing '+tor['state']+' torrent: '+tor['name'])

        if testmode == 0: # If not under test
            try:
                if OlderApi == 1:
                    payload = {'hashes': tor['hash']}
                    url = '/command/deletePerm'
                    response = requests.post(host+url,data=payload)
                    response.raise_for_status()
                    logging.debug('POST data: '+str(payload))
                else:
                    url = '/api/v2/torrents/delete?hashes='+str(tor['hash'])+'&deleteFiles=true'
                    response = requests.get(host+url)
                    response.raise_for_status()
            except requests.exceptions.RequestException as err:
                logging.error(str(err))
                exitcode = 1

    logging.debug('Exiting normally with code '+str(exitcode))

    if debugmode == 1:
        print('')
    exit(exitcode)

except requests.exceptions.RequestException as err:
    logging.error(str(err))
    if debugmode == 1:
        print('')
    exit(1)