#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Ganesh Bhat <ganesbha@cisco.com>"
__version__ = "2.0"
__date__ = "2016-Oct-13"

import sys
import re
import argparse
import os.path
import gzip

#-----------------------------------------------------------------------------#

# globals

loghog = "loghog"

parserInfo = '''

version     %s
date        %s
author      %s
''' % (__version__, __date__, __author__)

json_template = '''\
{
    "level": "%s",
    "log": {
            "line": "%s",
            "dt": "%s",
            "msg": "%s"
            },
    "mod": "%s"
},
'''

separator = "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"

logHighlights = ""
outPath = ""

keyCode = 0
keyMap = {
    '48' : '0',
    '49' : '1',
    '50' : '2',
    '51' : '3',
    '52' : '4',
    '53' : '5',
    '54' : '6',
    '55' : '7',
    '56' : '8',
    '57' : '9',
    '13' : 'select/ok',
    '27' : 'back',
    '33' : 'page+',
    '34' : 'page-',
    '38' : 'up',
    '40' : 'down',
    '37' : 'left',
    '39' : 'right',
    '458' : 'guide',
    '405' : 'A',
    '406' : 'B',
    '403' : 'C',
    '404' : 'D',
    '462' : 'menu',
    '457' : 'info',
    '409' : 'standby',
    '427' : 'ch+',
    '428' : 'ch-',
    '415' : 'play',
    '19'  : 'pause',
    '413' : 'stop',
    '416' : 'record',
    '417' : 'fwd',
    '412' : 'rew',
    '1073741868' : 'exit',
    '1073742341' : 'fav',
    '1073741981' : 'live',
    '1073741999' : 'last',
    '1073742336' : '#',
    '1073742337' : '*',
    '1073742340' : 'skip',
    '1073742341' : 'settings',
    '1073742342' : 'pip on/off',
    '1073742343' : 'pip swap',
    '1073742337' : 'pip move',
    '1073742345' : 'pip ch+',
    '1073742346' : 'pip ch-',
    '1073742347' : 'video source',
    '1073742359' : 'list',
    '1073742360' : 'day+',
    '1073742361' : 'day-'
}

boxType = ""
boxTypeMap = {
    '9k'  : 'G8 9K',
    '8k'  : 'G6 8K',
    '4k'  : 'G6 4K',
    '5k'  : 'G10 5K'
}

bfsInit = ""

vodPlaybackSpeedMap = {
    '100.000000'    : 'normal speed = 1x',
    '0.000000'      : 'paused speed = 0x',
    '750.000000'    : 'fast forward speed = 7.5x',
    '3000.000000'   : 'fast forward speed = 30x',
    '6000.000000'   : 'fast forward speed = 60x',
    '-750.000000'   : 'rewind speed = -7.5x',
    '-3000.000000'  : 'rewind speed = -30x',
    '-6000.000000'  : 'rewind speed = -60x'
}

#-----------------------------------------------------------------------------#

# functions

def jsonIt(lM, lMod, line, dT, msg):
    '''
    This function adds the log to json out. It also accounts for logMode and 
    formats it accordingly.
    
    DO NOT EDIT THIS
    '''

    fjson.write(json_template % (lM, line, dT, msg, lMod))

    return

#.............................................................................#

def htmlIt(lM, lMod, line, dT, msg):
    '''
    This function adds the log to html out. It also accounts for logMode and 
    does the higlighting accordingly.

    DO NOT EDIT THIS
    '''

    style = ''
    if  (lM == "SUCCESS"): style = 'style=background-color:DarkSeaGreen;'
    elif(lM == "WARN"):    style = 'style=background-color:LightSalmon;'
    elif(lM == "ERR"):     style = 'style=background-color:OrangeRed;'
    elif(lM == "FORCE"):   style = 'style=color:Cyan;'

    fhtml.write('<p '+style+'>')
    indent = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp'
    # fhtml.write(lMod + indent)
    if(line): fhtml.write(line + indent)
    if(dT):   fhtml.write(dT + indent)
    if(msg):  fhtml.write(msg)
    fhtml.write('\n</p>')

    return

#.............................................................................#

def logIt(message, logMode="INFO", logModule="GENERAL"):
    '''
    This is the internal logging function. This prints the message onto stdout
    and writes to .out file based on logging mode passed in the command line.

    DO NOT EDIT THIS
    '''

    htmlIt(logMode, logModule, '', '', message.rstrip('\n'))
    jsonIt(logMode, logModule, '', '', message.rstrip('\n'))
    print message
    return

#.............................................................................#

def dateTimeParser( line ):
    '''
    Date & Time from the log line is extraced here.
    Edit regex in this fucntion as needed.

    Ex: Following extracts out "Feb 12 09:30:00"
    '''
    
    dateTimePattern = re.compile("... .. ..:..:..")
    matchDateTime = re.search(dateTimePattern, line)
    try:
        dateTime = matchDateTime.group()
    except:
        return ""

    return dateTime

#.............................................................................#

def updateLog(line, parserName, message, logMode="INFO", logModule="GENERAL"):
    '''
    This function formats the log higlight as:
    [LoggingMode] [LoggingModule] Line# : DateTime : Message

    It calls logIt to display log on stdout and writes to .out.
    
    DO NOT EDIT THIS
    '''

    global logHighlights

    line = line.rstrip('\n')
    dateTimeInfo = dateTimeParser(line)
    lineInfo = "line " + str(lineCount+1)

    highlight = lineInfo.ljust(13) + dateTimeInfo.ljust(18) + message + "\n"
    htmlIt(logMode, logModule, lineInfo, dateTimeInfo, message)
    jsonIt(logMode, logModule, lineInfo, dateTimeInfo, message)
    logHighlights += highlight
    print logMode.ljust(10) + highlight.rstrip('\n')

    return

#.............................................................................#

def regexParser(line, regexList, logMode, logModule):
    '''
    This is the generic regular expression parser which searches the supplied
    regex pattern in the log line  and substitutes it with alternate text that 
    is provided. It does this for all the regex's in regexList.

    Args:
    line        actual log line to search regex
    regexList   list of regular expression to be matched & substituted
    logMode     logging mode of the regex
    logModule   logging module of the regex

    DO NOT EDIT THIS
    '''

    pattern = re.compile("^.*" + regexList[0][0] + ".*$")
    match = re.search(pattern, line)

    if match:
        logStr = match.group()
        
        for regex in regexList:
            val = re.sub(regex[0], regex[1], logStr)
            val = val.strip()
            logStr = val

        updateLog(line, sys._getframe().f_code.co_name, logStr, logMode, logModule)
        return True

    return False

#.............................................................................#

def keyPressParser(line, logMode, logModule):
    # Jan 27 16:53:41 powertv syslog: DLOG|GALIO|NORMAL| -- sending key 462 --
    global keyCode

    pattern = re.compile("^.*\| -- sending key .* --.*$")
    match = re.search(pattern, line)

    if match:
        val = re.sub(' --', '', re.sub('^.*\| -- sending key ', '', match.group()))
        val = val.strip()
        
        try:
            val = keyMap[val]
        except:
            val = val
        
        if (keyCode == val):
            keyCode = ""
            return True
        
        keyCode = val
        logStr = "Key Press : "
        updateLog(line, sys._getframe().f_code.co_name, logStr + val, logMode, logModule)
        return True
    return False

#.............................................................................#

def bfsInitDoneParser(line, logMode, logModule):
    #Jan 25 10:47:55 powertv syslog: DLOG|BFSUTILITY|EMERGENCY|BFS Init Done!
    global bfsInit

    pattern = re.compile("^.*\|BFS Init Done!.*$")
    match = re.search(pattern, line)

    if match:
        val = re.sub('^.*\|BFS', 'BFS', match.group())
        val = val.strip()

        if (bfsInit == val):
            return True

        bfsInit = val
        logStr = ""
        updateLog(line, sys._getframe().f_code.co_name, logStr + val, logMode, logModule)
        return True
    return False

#.............................................................................#

def recordingFailureParser(line, logMode, logModule):
    # Dec 29 10:09:33 powertv syslog: DLOG|DVR|Recording Failure|FDR_log: DVRTXN080030: 1006|Liberty's Kids|17|1450921500|RECORDING DELETED:DISK SPACE CRITICAL 95%
    # Jan 25 06:00:04 powertv csp_CPERP: DLOG|DVR|Recording Failure|TimerHandler: Failure not enough disk space to record Breakfast Television AID 113
    # Jan 13 21:19:16 powertv csp_CPERP: DLOG|DVR|Recording Failure|FDR_log: DVRTXN050030: CLM UPDATE START
    # Jan 13 21:19:38 powertv csp_CPERP: DLOG|DVR|Recording Failure|FDR_log: DVRTXN050040: CLM UPDATE SUCCESS
    
    pattern = re.compile("^.*Recording Failure.*$")
    match = re.search(pattern, line)

    if match:
        val = re.sub('^.*RECORDING DELETED:DISK SPACE CRITICAL', 'disk space critical', match.group())
        if (val == match.group()):
            val = re.sub('^.*Failure not', 'not', match.group())
            if (val == match.group()):
                val = re.sub('^.*CLM UPDATE START', 'Channel Map update has started', match.group())
                if (val == match.group()):
                    val = re.sub('^.*CLM UPDATE SUCCESS', 'Channel Map update successful', match.group())
        val = val.strip()

        logStr = "recording failed : "
        updateLog(line, sys._getframe().f_code.co_name, logStr + val, logMode, logModule)
        return True
    return False

#.............................................................................#

def vodPlaybackParser(line, logMode, logModule):
    # Jan 29 11:12:30 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:1 Den:1 Speed:100.000000 #####
    # Jan 29 11:21:18 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:0 Den:0 Speed:0.000000 #####
    # Jan 29 11:22:26 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:15 Den:2 Speed:750.000000 ####
    # Jan 29 11:27:22 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:300 Den:10 Speed:3000.000000 #####
    # Jan 29 11:27:26 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:600 Den:10 Speed:6000.000000 #####
    # Jan 29 11:23:27 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:-15 Den:2 Speed:-750.000000 #####
    # Jan 29 11:27:56 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:-300 Den:10 Speed:-3000.000000 #####
    # Jan 29 11:28:00 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:-600 Den:10 Speed:-6000.000000 #####

    pattern = re.compile("^.*OnDemand.*HandleCallback.*Speed:.*$")
    match = re.search(pattern, line)

    if match:
        val = re.sub(' ####.*$', '', re.sub('^.*OnDemand.*HandleCallback.*Speed:', '', match.group()))
        val = val.strip()

        try:
            val = vodPlaybackSpeedMap[val]
        except:
            val = val

        logStr = "vod playback ongoing at "
        updateLog(line, sys._getframe().f_code.co_name, logStr + val, logMode, logModule)
        return True
    return False

#.............................................................................#
 
def stackTraceParser(line, logMode, logModule):
    # _log@package://7FA25FD0-9FD544F5/js/lib/console.js:75
    # warn@package://7FA25FD0-9FD544F5/js/lib/console.js:161
    # initialize@package://7FA25FD0-9FD544F5/js/app.js:1801
    # initializeVOD@package://7FA25FD0-9FD544F5/vod.html:103
    # onload@package://7FA25FD0-9FD544F5/vod.html:118
    # _log@package://7FA25FD0-9FD544F5/js/lib/console.js:75
    # error@package://7FA25FD0-9FD544F5/js/lib/console.js:165
    # initialize@package://7FA25FD0-9FD544F5/js/app.js:1802
    # initializeVOD@package://7FA25FD0-9FD544F5/vod.html:103
    # onload@package://7FA25FD0-9FD544F5/vod.html:118

    pattern = re.compile("^.*\@package:\/\/")
    match = re.search(pattern, line)
    
    if match:
        val = line.strip()

        logStr = "Stack trace : "
        updateLog(line, sys._getframe().f_code.co_name, logStr + val, logMode, logModule)
        return True
    return False

#.............................................................................#

def typeErrorParser(line, logMode, logModule):
    # Jan 29 13:00:53 powertv syslog: DLOG|GALIO|ERROR|package://5415C3E6-8DBEB1FC/js/zapp.js at line 2831 TypeError: Result of expression 'TVLib.Event.MOMMessage.VOD1080p' [undefined] is not an object.
    # Mar 24 11:38:10 powertv csp_CPERP: DLOG|GALIO|ERROR|antclient://library/js/widget_actionbarheader.js at line 44 TypeError: Result of expression near ‘...}}}}.bind(this)...' [])

    pattern = re.compile("^.*\|GALIO\|ERROR\|.* TypeError: .*$")
    match = re.search(pattern, line)

    if match:
        logStr = match.group()
        
        val = re.sub("^.*\|GALIO\|ERROR\|", '', logStr)
        val = val.strip()
        logStr = "Error in UI : "

        updateLog(line, sys._getframe().f_code.co_name, logStr + val, logMode, logModule)
        return True
    
    return False

#.............................................................................#

def appShownParser(line, logMode, logModule):
    # Mar 23 10:19:43 powertv syslog: DLOG|GALIO|NORMAL|package://E1E7B6D5-9D658D76/js/controller.js at line 128 RTNUI : controllerShowApp( vod )
    pattern = re.compile("^.*RTNUI : controllerShowApp\( .*$")
    match = re.search(pattern, line)

    if match:
        logStr = match.group()

        val = re.sub("^.*RTNUI : controllerShowApp\( ", '', logStr)
        val = re.sub(" \).*$", '', val)
        val = val.strip()

        appsToShow = ["setup", "ipg", "vod", "pvr", "settings", "pc"]
        if (val in appsToShow):
            logStr = "Showing app : "
            updateLog(line, sys._getframe().f_code.co_name, logStr + val, logMode, logModule)
        return True

    return False

#.............................................................................#
 
def appHiddenParser(line, logMode, logModule):
    # Mar 23 10:24:16 powertv syslog: DLOG|GALIO|NORMAL|package://E1E7B6D5-9D658D76/js/controller.js at line 536 RTNUI : controllerApplicationHidden(appInfo)vod
    pattern = re.compile("^.*RTNUI : controllerApplicationHidden\(appInfo\).*$")
    match = re.search(pattern, line)

    if match:
        logStr = match.group()

        val = re.sub("^.*RTNUI : controllerApplicationHidden\(appInfo\)", '', logStr)
        val = val.strip()

        appsToShow = ["setup", "ipg", "vod", "pvr", "settings", "pc"]
        if (val in appsToShow):
            logStr = "Hiding app : "
            updateLog(line, sys._getframe().f_code.co_name, logStr + val, logMode, logModule)
        return True

    return False

#.............................................................................#
  
# parser structure

#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
# # sample log line 
# [
#     [
#         ['regex to find',  'string to replace regex'],
#         ['regex2 to find', ''],
#        
#         ...
#         ...
#         ...
#
#         ['regexN to find', '']
#     ],
#     "INFO"/"SUCESS"/"WARN"/"ERR",
#     "GENERAL"/"BOOT"/"BFS"/"LIVE"/"VOD"/"PVR"/"REC"/"KEYS"/"SEARCH"
# ]
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
# # sample log line
# [
#     specific_parser_function,
#     "INFO"/"SUCESS"/"WARN"/"ERR",
#     "GENERAL"/"BOOT"/"BFS"/"LIVE"/"VOD"/"PVR"/"REC"/"KEYS"/"SEARCH"
# ]
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#


parsers = [
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 27 16:53:41 powertv syslog: DLOG|GALIO|NORMAL| -- sending key 462 --
            [
                keyPressParser,
                "INFO",
                "KEYS"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Image created for 9k box.
            [
                [
                    ['^Image created for ', 'Box type : '],
                    [' box.*$', '']
                ],
                "INFO",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 25 10:47:55 powertv syslog: DLOG|BFSUTILITY|EMERGENCY|BFS Init Done!
            [
                bfsInitDoneParser,
                "SUCCESS",
                "BFS"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 27 11:23:28 powertv syslog: DLOG|BFS_GET_MODULE|EMERGENCY|get_filter_setting_for_module - 625 assertion failed
            [
                [
                    ['^.* - 625 assertion failed$', 'BFS dnld crash CSCux30595']    
                ],
                "WARN",
                "BFS"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 20 12:28:14 powertv csp_CPERP: DLOG|BFS_GET_MODULE|ERROR|bool CSCI_BFS_API::ActiveContext::_serializeAndSendPacket(int, BfsIpc::PacketBuilder&) - 222 Error sending eIpc_BeginDownload packet to BFS server - send /tmp/bfs_server error Broken pipe
            [
                [
                    ['^.*BFS.* error Broken pipe$', 'BFS error broken pipe']    
                ],
                "WARN",
                "BFS"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 11:17:18 powertv epg: DLOG|EPG_LOAD|SIGNIFICANT_EVENT|gi_load: GI for day 2 not found either in disk cache nor memory cache, check wheather it is loading
            [
                [
                    ['^.*gi_load: GI for day.*not found.*$', 'BFS is up but NOT able to download EPG data']    
                ],
                "WARN",
                "BFS"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 12:20:13 powertv syslog: doc_StoreParameter: Host IPv4 address: 100.109.176.144.
            [
                [
                    ['^.*: Host IPv4 address: ', 'IP Address : ']
                ],
                "SUCCESS",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 12:19:15 powertv syslog: DLOG|MDA|ERROR|mda_network_init:336: MAC address = 68:EE:96:6F:15:B8
            [
                [
                    ['^.*mda_network_init.*MAC address = ', 'MAC Address : ']
                ],
                "SUCCESS",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 13:02:57 powertv syslog: DLOG|MSP_MPLAYER|EMERGENCY|IMediaPlayer:IMediaPlayerSession_PersistentRecord:685 sess: 0x3ab3ee0  recordUrl: sadvr://dElWnhPo  start: 0.000000   stop: -2.000000    **SAIL API**
            [
                [
                    ['^.*IMediaPlayer:IMediaPlayerSession_PersistentRecord.*recordUrl.*$', 'recording started']
                ],
                "SUCCESS",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 27 11:24:56 powertv syslog: DLOG|GALIO|NORMAL|SCHED: record added dvr://recording/00000000-0000-0000-0000-00000000000000000570 rec [@01a57220: dvr://recording/00000000-0000-0000-0000-00000000000000000570 play 1 state mom_recording_RECORDING rel @01a57ee0 The Price Is Right]
            [
                [
                    ['^.*GALIO\|NORMAL.*record added.*_RECORDING rel @........ ', 'start recording program : '],
                    ['].*$', '']
                ],
                "SUCCESS",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 13:04:28 powertv syslog: DLOG|MSP_MRDVR|ERROR|MRDvrServer:Csci_Msp_MrdvrSrv_NotifyRecordingStop:112 URL is : sctetv://003
            [
                [
                    ['^.*Csci_Msp_MrdvrSrv_NotifyRecordingStop.*$', 'recording stopped']
                ],
                "SUCCESS",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 15:12:42 powertv syslog: DLOG|GALIO|NORMAL|SCHED: record updated dvr://recording/00000000-0000-0000-0000-00000000000000000641 rec [@03989318: dvr://recording/00000000-0000-0000-0000-00000000000000000641 play 1 state mom_recording_STOPPED rel <NULL> Zooville]
            [
                [
                    ['^.*GALIO\|NORMAL.*record updated.*_STOPPED rel <NULL> ', 'stop recording program : '],
                    ['].*$', '']
                ],
                "INFO",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 13:05:15 powertv syslog: DLOG|DVRUTIL|ERROR|Successfully Deleted file /mnt/dvr0/vNA4T1Rn
            [
                [
                    ['^.*DVRUTIL.*Successfully Deleted file.*$', 'recording deleted']
                ],
                "WARN",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 15:19:06 powertv syslog: DLOG|GALIO|NORMAL|SCHED: record deleted (state != mom_recording_RECORDING) dvr://recording/00000000-0000-0000-0000-00000000000000000641 rec [@03989318: dvr://recording/00000000-0000-0000-0000-00000000000000000641 play 1 state mom_recording_STOPPED rel <NULL> Zooville]
            [
                [
                    ['^.*GALIO\|NORMAL.*record deleted.*_STOPPED rel <NULL> ', 'reording deleted : '],
                    ['].*$', '']
                ],
                "WARN",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 13:11:57 powertv syslog: DLOG|MSP_MPLAYER|EMERGENCY|IMediaPlayer:IMediaPlayerSession_Load:434  URL: sadvr://mnt/dvr0/6oxGuu4M  session: 0x1b0a978     **SAIL API**
            [
                [
                    ['^.*IMediaPlayer:IMediaPlayerSession_Load.*URL: sadvr:.*$', 'recording playback started']
                ],
                "SUCCESS",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 15:14:01 powertv syslog: DLOG|GALIO|NORMAL|package://5415C3E6-8DBEB1FC/js/zapp_modes.js at line 375 ZapperModeVideo::Connect is now Playing [object MOMScheduledRecording] : Name : dvr://recording/00000000-0000-0000-0000-00000000000000000641 : Zooville
            [
                [
                    ['^.*GALIO\|NORMAL.*Connect is now Playing.*dvr.* : ', 'recording playback started = ']
                ],
                "SUCCESS",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 29 10:09:33 powertv syslog: DLOG|DVR|Recording Failure|FDR_log: DVRTXN080030: 1006|Liberty's Kids|17|1450921500|RECORDING DELETED:DISK SPACE CRITICAL 95%
            # Jan 25 06:00:04 powertv csp_CPERP: DLOG|DVR|Recording Failure|TimerHandler: Failure not enough disk space to record Breakfast Television AID 113
            # Jan 13 21:19:16 powertv csp_CPERP: DLOG|DVR|Recording Failure|FDR_log: DVRTXN050030: CLM UPDATE START
            # Jan 13 21:19:38 powertv csp_CPERP: DLOG|DVR|Recording Failure|FDR_log: DVRTXN050040: CLM UPDATE SUCCESS
            [
                recordingFailureParser,
                "ERR",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 22 16:14:53 powertv syslog: DLOG|MSP_DVR|ERROR|RecSession:stopConvert:808 RecordSessionStateError: Error Bad state: 3
            [
                [
                    ['^.*RecordSessionStateError: Error Bad state: 3$', 'Recording not playable : Error Bad state: 3']
                ],
                "WARN",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Nov 13 10:49:26 powertv csp_CPERP: DLOG|CA_CAK|NORMAL|****** ECM 16 Digital_Response, result 0xb
            [
                [
                    ['^.*ECM 16 Digital_Response, result 0xb$', 'Recording not playable : due to deauthorization']
                ],
                "WARN",
                "REC"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 11 09:26:29 powertv csp_CPERP: DLOG|MSP_MPLAYER|ERROR|DisplaySession:stop:1352 cpe_media_Stop error -19
            [
                [
                    ['^.*cpe_media_Stop error -19$', 'Black Screen on all channels : due to cpe_media_Stop2 error -19 CSCup37738']
                ],
                "WARN",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 21 15:35:08 powertv csp_CPERP: DLOG|MSP_MPLAYER|ERROR|Zapper:handleEvent:225 PsiTimeOutError: Warning - PSI not available. DoCallback – ContentNotFound!!
            [
                [
                    ['^.*PSI not available.*$', 'VOD playback black screen : due to stream issue']
                ],
                "WARN",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 20 03:50:21 powertv csp_CPERP: DLOG|MSP_MPLAYER|EMERGENCY|Zapper:handleEvent:220 Warning - Tuner lock timeout.May be signal strength is low or no stream on tuned frequency!!
            [
                [
                    ['^.*signal strength is low or no stream.*$', 'Black screen : stream issue - low signal or no stream']
                ],
                "WARN",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 11 15:36:10 powertv syslog: DLOG|MSP_PSI|ERROR|Psi:dispatchEvent:125 PsiTimeOutError: Time out while waiting for PAT
            [
                [
                    ['^.*PsiTimeOutError: Time out while waiting for PAT$', 'Black screen : PAT timeout']
                ],
                "WARN",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Nov 11 00:10:17 powertv csp_CPERP: DLOG|MSP_MPLAYER|ERROR|Zapper:GetComponents:1717 PSI/PMT Info Not found
            [
                [
                    ['^.*PMT Info Not found$', 'Black screen : stream issue - no pmt']
                ],
                "WARN",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 31 19:01:37 powertv csp_CPERP: DLOG|SAM|ERROR|Thread Setname Failed:threadRetValue:0
            [
                [
                    ['^.*SAM.*Thread Setname Failed.*$', 'Stuck at -04- : due to SAM not ready']
                ],
                "WARN",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Nov 21 05:25:25 powertv csp_CPERP: DLOG|MSP_DVR|ERROR|dvr:dispatchEvent:1022 Service DeAuthorized by CAM
            [
                [
                    ['^.*Service DeAuthorized by CAM$', 'Service deauthorized']
                ],
                "WARN",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Nov 21 05:25:25 powertv csp_CPERP: DLOG|CA_CAK|ERROR|PkCakDvrRecordSession_cronus.cpp:383 Async No authorized ECM in CA message
            [
                [
                    ['^.*No authorized ECM in CA message$', 'Black screen due to no authorized ECM in CA message']
                ],
                "WARN",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Nov 13 01:43:41 powertv syslog: DLOG|SDV|ERROR|ccmisProtocol.cpp HandleProgramSelectIndication Channel is not available
            [
                [
                    ['^.*Channel is not available$', 'Channel is not available']
                ],
                "WARN",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Nov 12 21:20:30 powertv bfsdnld: DLOG|BFS_GET_MODULE|ERROR|directory_update_timeout directory update taking more than 120 seconds
            [
                [
                    ['^.*directory update taking more than 120 seconds.*$', 'Stuck on -05- due to ui error loading']
                ],
                "WARN",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb  1 10:04:55 powertv syslog:  Settop Extender Bridge: UpnPInitializeSSLContext - Retrying (# 182) to get DOCSIS cert info!
            [
                [
                    ['^.*Retrying .* to get DOCSIS cert info.*$', 'Stuck on -05- due to failure in getting docsis cert info']
                ],
                "WARN",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Sep 11 15:08:44 powertv root: SCRIPT: unhandled exception: Attempt to convert null or undefined value recording to Object
            # Sep 11 19:08:52 powertv root: SCRIPT: unhandled exception: SETTINGS.CheckboxPane() is not defined
            [
                [
                    ['^.*SCRIPT: unhandled exception.*$', 'exception in rtnui !!!']
                ],
                "ERR",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 12:47:57 powertv syslog: DLOG|DNCS_SETTINGS|EMERGENCY|SetStagingstatus:94 isStagingDefsApplied: 0 isHubSpecficStagingDefsApplied: 1 isAddressableStaged: 0
            [
                [
                    ['^.*SetStagingstatus.* isStagingDefsApplied: 0.*$', 'Stuck on -05- after Factory Restore due to not staged']
                ],
                "WARN",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb  1 11:26:52 powertv csp_CPERP: DLOG|DLM|NORMAL|[downloadAppAndArtFile][96] Value of sam_isGrpDefParsed from BFS() = 0
            [
                [
                    ['^.*downloadAppAndArtFile.* Value of sam_isGrpDefParsed from.* = 0.*$', 'Stuck on -05- download manager is blocked on downloading grps_defs.txt']
                ],
                "WARN",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 31 19:01:13 powertv syslog: DLOG|SAILMSG|ERROR|Bootup profiling:      Application started => Waiting for SessInit : 49.64 seconds, total time: 91.46 seconds (BUFFERED)
            # Dec 31 19:01:29 powertv syslog: DLOG|SAILMSG|ERROR|Bootup profiling: -00- SessInit is ready => Waiting for Hub Id : 2.02 seconds, total time: 93.48 seconds (BUFFERED)
            # Dec 31 19:01:29 powertv syslog: DLOG|SAILMSG|ERROR|Bootup profiling: -01- Hub Id is ready => Waiting for SI : 15.04 seconds, total time: 108.53 seconds (BUFFERED)
            # Jan 27 11:21:07 powertv syslog: DLOG|SAILMSG|ERROR|Bootup profiling: -02- SI is ready => Waiting for BFS : 65.44 seconds, total time: 173.96 seconds (BUFFERED)
            # Jan 27 11:21:07 powertv syslog: DLOG|SAILMSG|ERROR|Bootup profiling: -03- BFS is ready => Waiting for SAM : 0.02 seconds, total time: 173.99 seconds
            # Jan 27 11:21:09 powertv syslog: DLOG|SAILMSG|ERROR|Bootup profiling: -04- SAM is ready => Waiting for global config : 2.03 seconds, total time: 176.01 seconds
            # Jan 27 11:21:16 powertv syslog: DLOG|SAILMSG|ERROR|Bootup profiling: -05- Global config is ready => Launching UI : 2.02 seconds, total time: 178.03 seconds
            # Jan 27 11:24:50 powertv syslog: DLOG|SAILMSG|ERROR|Bootup profiling:      UI launched => System ready : 218.45 seconds, total time: 396.48 seconds
            [
                [
                    ['^.*Bootup profiling: ', 'Bootup step : '],
                    [' =>.*$', '']
                ],
                "SUCCESS",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 12:21:13 powertv syslog: DLOG|SPM_VODCTLG|ERROR|vod-internal.cpp:void* tr_VodInit(void*):959: Network is two way and System is Ready
            [
                [
                    ['^.*Network is two way and System is Ready.*$', 'Network is two way and System is Ready']
                ],
                "SUCCESS",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 12:22:01 powertv syslog: DLOG|DLM|EMERGENCY|[sendSailMessage][1517] dlmWarningType:MAINT_DOWNLOAD_WARNING
            # Jan 28 12:22:21 powertv syslog: DLOG|DLM|EMERGENCY|[sendSailMessage][1517] dlmWarningType:MAINT_DOWNLOAD_REQUEST
            # Jan 28 12:23:00 powertv syslog: DLOG|DLM|EMERGENCY|[sendSailMessage][1517] dlmWarningType:MAINT_DOWNLOAD_COMPLETE
            # Feb 15 15:24:00 powertv csp_CPERP: DLOG|DLM|EMERGENCY|[sendSailMessage][1494] dlmWarningType:MAINT_DOWNLOAD_ERROR
            [
                [
                    ['^.*MAINT_DOWNLOAD_', 'Maintenance download : ']
                ],
                "WARN",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 14:41:31 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|SeaChange_SessCntrl:HandleSessionConfirmResp:915 WARNING - SERVER NOT READY - Invalid DSMCC response received : 6 !!
            [
                [
                    ['^.*SERVER NOT READY - Invalid DSMCC response.*$', 'vod session setup failed - vod server not ready']
                ],
                "ERR",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 10:55:23 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|VOD_SessCntl(TID:5470b340):ProcessTimeoutCallBack:415  NOT RECEIVED SERVER RESPONSE  - sending error to service layer !!
            [
                [
                    ['^.*VOD_SessCntl.* NOT RECEIVED SERVER RESPONSE.*$', 'vod session setup failed - no response from vod server']
                ],
                "ERR",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 10:38:33 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|StreamTearDown:122 Closing the socket[400]
            [
                [
                    ['^.*StreamTearDown.*Closing the socket.*$', 'vod session torn down. It is normal if vod playback was stopped']
                ],
                "WARN",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 10:53:52 powertv syslog: DLOG|MSP_MPLAYER|EMERGENCY|IMediaPlayer:IMediaPlayerSession_Load:434  URL: lscp://AssetId=1135&AppId=524289&BillingId=0&PurchaseTime=1454082831&RemainingTime=85482&EndPos=5635&srmManufacturer=Seachange&streamerManufacturer=Seachange&connectMgrIp=0x4161e479&Title=ForestGumpMultiTrick3 - 60x  session: 0x1b143b0     **SAIL API**
            # Feb  1 16:36:47 powertv syslog: DLOG|GALIO|NORMAL|package://5415C3E6-9E841FCC/js/zapp_modes.js at line 375 ZapperModeVideo::Connect is now Playing [object MOMVODAsset] : Name : undefined : ForestGumpMultiTrick3 - 60x
            [
                [
                    ['^.*IMediaPlayer:IMediaPlayerSession_Load.*AssetId.*Title=', 'vod playback of asset : '],
                    [' session.*$', '']
                ],
                "SUCCESS",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 11:12:30 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:1 Den:1 Speed:100.000000 #####
            # Jan 29 11:21:18 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:0 Den:0 Speed:0.000000 #####
            # Jan 29 11:22:26 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:15 Den:2 Speed:750.000000 ####
            # Jan 29 11:27:22 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:300 Den:10 Speed:3000.000000 #####
            # Jan 29 11:27:26 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:600 Den:10 Speed:6000.000000 #####
            # Jan 29 11:23:27 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:-15 Den:2 Speed:-750.000000 #####
            # Jan 29 11:27:56 powertv syslog: DLOG|MSP_ONDEMAND|ERROR|OnDemand(TID:5470b340):HandleCallback:1263 #### Ondemand ::Callback signal for Num:-300 Den:10 Speed:-3000.000000 #####
            [
                vodPlaybackParser,
                "INFO",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 14:46:11 powertv syslog: DLOG|GALIO|NORMAL|antclient://library/js/gadget_baseinfo.js at line 99 In base info update Programme Name is : General Hosp. : CHANNEL NUMBER : 7
            [
                [
                    ['^.*gadget_baseinfo.* Programme Name is : ', 'Tuned to program : ']
                ],
                "INFO",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 14:46:11 powertv syslog: DLOG|GALIO|NORMAL|antclient://library/js/gadget_baseinfo.js at line 340 RTNUI : gadget_baseinfo : reallyUpdate : 7 <span>CITYT</span>
            [
                [
                    ['^.*gadget_baseinfo : reallyUpdate : ', 'Tune to channel : '],
                    ['<\/?span>', '']
                ],
                "INFO",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 29 12:54:18 powertv syslog: DLOG|MSP_MPLAYER|EMERGENCY|IMediaPlayer:IMediaPlayerSession_Load:434  URL: sctetv://022  session: 0x1c6f4f8     **SAIL API**
            [
                [
                    ['^.*IMediaPlayer:IMediaPlayerSession_Load.*sctetv:\/\/', 'Tuned to channel : '],
                    [' session.*$', '']
                ],
                "INFO",
                "LIVE"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan 28 12:20:36 powertv syslog: DLOG|GALIO|NORMAL|antclient://library/js/config.js at line 2039 RTNUI : Communication mode has been updated to : docsis : new IP Address : 100.109.176.144
            [
                [
                    ['^.*Communication mode has been updated to : docsis.*$', 'Communication mode has been updated to : docsis']
                ],
                "SUCCESS",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb  1 10:04:31 powertv syslog: DLOG|DIAG_WS_PRIVATE|ERROR|(Not an Error) Informative: [UpdateLogFwdState][392]Box is either in davic mode or in one way!!!!! Disabling the log forwarding feature]
            # [
            #     [
            #         ['^.*Box is either in davic mode or in one way.*$', 'Box in DAVIC mode or in one way']
            #     ],
            #     "INFO",
            #     "BOOT"
            # ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb  9 16:32:35 powertv syslog: DLOG|GALIO|NORMAL|package://5F2DD257-C79E59BB/js/debug.js at line 7 [] - 16:32:35.832 - [I]: logging for ZTAP turned off
            # Feb  9 16:32:36 powertv syslog: DLOG|GALIO|NORMAL|package://5F2DD257-C79E59BB/js/debug.js at line 7 [] - 16:32:36.666 - [I]: logging for ZTAP turned on
            [
                [
                    ['^.* logging for ZTAP turned ', 'Zodiac logging tunred ']
                ],
                "INFO",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb  9 16:36:32 powertv syslog: DLOG|GALIO|NORMAL|package://5F2DD257-C79E59BB/js/debug.js at line 7 [ZSEA] - 16:36:32.648 - [D]: request(searchObjectOrText: ABC)
            [
                [
                    ['^.*ZSEA.*searchObjectOrText: ', 'Searching for : '],
                    ['\).*$', '']
                ],
                "INFO",
                "SEARCH"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb  9 16:35:34 powertv syslog: DLOG|GALIO|NORMAL|package://5F2DD257-C79E59BB/js/debug.js at line 7 [ZSEA] - 16:35:34.432 - [D]: onResultsEnter [PERSONALITY] [<em>A</em>ngela <em>B</em>assett]
            # Feb  9 16:37:50 powertv syslog: DLOG|GALIO|NORMAL|package://5F2DD257-C79E59BB/js/debug.js at line 7 [ZSEA] - 16:37:50.775 - [D]: onResultsEnter [PERSONALITY] [<em>A</em>lexander <em>B</em>.<em>C</em>ollett]
            [
                [
                    ['^.*ZSEA.*onResultsEnter \[PERSONALITY\] ', 'search asset selected : '],
                    ['\<em\>', ''],
                    ['\<\/em\>', '']
                ],
                "INFO",
                "SEARCH"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 31 19:00:50 powertv syslog: davact_StoreParameter: set operation mode to kCss_DAVICStandardOpMode(1)
            [
                [
                    ['^.*davact_StoreParam.*OpMode\(1\).*$', 'boot in DAVIC to start out']
                ],
                "INFO",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 31 19:00:50 powertv syslog: davact_StoreParameter: set direction mode to kCss_OOBDirMode(1)
            [
                [
                    ['^.*davact_Store.*OOBDirMode\(1\).*$', 'Communication mode : one way']
                ],
                "INFO",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Dec 31 19:00:50 powertv syslog: davact_StoreParameter: set mac boot mode to kCss_SlowMacBootMode(1)
            [
                [
                    ['^.*davact_Store.*SlowMacBootMode\(1\).*$', 'start in slow boot']
                ],
                "INFO",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb 11 09:49:33 powertv syslog: vpod_cccm_ProcCccmEvent() Scheduling failSafeTimerID
            [
                [
                    ['^.*vpod_cccm.*Scheduling failSafeTimerID.*$', 'start of 20min failsafe timer']
                ],
                "INFO",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb 11 09:49:33 powertv syslog: doc_StoreParameter: set operation mode to kCss_DOCSISIpDirectQpskOpMode(11) 
            [
                [
                    ['^.*set operation mode to kCss_DOCSISIpDirectQpskOpMode\(11\).*$', 'try to go to DOCSIS']
                ],
                "INFO",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb 11 09:49:33 powertv syslog: doc_StoreParameter: set direction mode to kCss_OOBInteractiveDirMode(3)
            [
                [
                    ['^.*set direction mode to kCss_OOBInteractiveDirMode\(3\).*', 'go 2way']
                ],
                "SUCCESS",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Feb 11 09:50:02 powertv syslog: vpod_cccm_ProcCccmEvent() Cancelling failSafeTimerID 43 because CM is in TwoWay Operational Mod 
            [
                [
                    ['^.*Cancelling failSafeTimerID .* TwoWay Operational.*', 'Cancel failsafe as CM is in 2way mode']
                ],
                "INFO",
                "BOOT"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jan  1 00:00:32 powertv root: version name: 6.0.0.0132
            [
                [
                    ['^.*version name: ', 'RTN build version = ']
                ],
                "SUCCESS",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Mar 22 19:38:02 GALIO|ERROR|package://7FA25FD0-9FD544F5/js/lib/console.js at line 78 [VOD VOD.Application] [ERROR] VOD - LOG ERROR
            [
                [
                    ['^.*\[VOD .*\] \[ERROR\]', 'VOD app encountered error : ']
                ],
                "ERR",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Mar 22 19:38:02 GALIO|ERROR|package://7FA25FD0-9FD544F5/js/lib/console.js at line 78 [VOD VOD.Application] [WARN] VOD - LOG WARNING
            [
                [
                    ['^.*\[VOD .*\] \[WARN\]', 'VOD app encountered warning : ']
                ],
                "WARN",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Apr  7 12:53:39 powertv csp_CPERP: DLOG|GALIO|NORMAL|>>>> VOD-T3 - 1460048019362 - 1ms - 2952ms - vod-dialog.js - Showing dialog box - unknown-catalogue
            [
                [
                    ['^.*vod-dialog.js - Showing dialog box - ', 'VOD dialogue box presented : ']
                ],
                "WARN",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # _log@package://7FA25FD0-9FD544F5/js/lib/console.js:75
            [
                stackTraceParser,
                "ERR",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Mar 24 11:38:10 powertv csp_CPERP: DLOG|GALIO|ERROR|antclient://library/js/widget_actionbarheader.js at line 44 TypeError: Result of expression near ‘...}}}}.bind(this)...' [undefined] is not a function.])
            [
                typeErrorParser,
                "ERR",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Mar 23 10:19:43 powertv syslog: DLOG|GALIO|NORMAL|package://E1E7B6D5-9D658D76/js/controller.js at line 128 RTNUI : controllerShowApp( vod )
            [
                appShownParser,
                "INFO",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Mar 23 10:24:16 powertv syslog: DLOG|GALIO|NORMAL|package://E1E7B6D5-9D658D76/js/controller.js at line 536 RTNUI : controllerApplicationHidden(appInfo)vod
            [
                appHiddenParser,
                "INFO",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Mar 23 10:22:55 powertv syslog: DLOG|GALIO|MINOR_DEBUG|package://73E5D7AD-9D658EF7/js/views/grid/grid-manager.js at line 30 ::::: displayName=New Releases 
            # Apr  7 12:53:10 powertv csp_CPERP: DLOG|GALIO|NORMAL|>>>> VOD-T3 - 1460047990578 - 42ms - 45ms - grid-item.js - Select grid tile - Rogers On Demand Catalogue
            [
                [
                    ['^.* Select grid tile - ', 'Entering VOD catalogue : ']
                ],
                "INFO",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Mar 23 10:28:31 powertv syslog: DLOG|GALIO|MINOR_DEBUG|package://73E5D7AD-9D658EF7/js/lib/vod/vod-lib-client.js at line 83 USVOD In isPartOfCatalogue() The Search Term is:::Alvin and the Chipmunks: The Road Chip ,0x642b
            [
                [
                    ['^.*The Search Term is:::', 'VOD asset selected : '],
                    ['\,0x642b.*$', '']
                ],
                "INFO",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Mar 28 17:38:41 powertv csp_CPERP: DLOG|GALIO|NORMAL|package://E3D7D173-BF201ADE/js/lib/console.js at line 60 [VOD VOD.Lib.ApiManager] [DEBUG] api-manager.js - Received MOM_ContentCatalogue event
            [
                [
                    ['^.*VOD .*DEBUG.* Received MOM_ContentCatalogue event', 'VOD app received MOM_ContentCatalogue event, resetting all catalogues']
                ],
                "SUCCESS",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Mar 28 17:38:41 powertv csp_CPERP: DLOG|GALIO|NORMAL|package://E3D7D173-BF201ADE/js/lib/console.js at line 60 [VOD VOD.Lib.ApiManager] [DEBUG] api-manager.js - Received MOM_ContentCatalogue event
            [
                [
                    ['^.*MOM_ContentCatalogue', 'VOD app received MOM_ContentCatalogue event, resetting all catalogues based on this']
                ],
                "SUCCESS",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            #Jul 18 00:05:10 powertv syslog: DLOG|GR|ERROR|file open success for file graceful_reboot_required, Adding trigger: Syslog_Graceful_Reboot
            [
                [
                    ['^.*graceful_reboot_required\,', 'Graceful Reboot Required : '],
                ],
                "ERR",
                "GENERAL"
            ], 
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            #Jul 16 10:16:09 powertv syslog: DLOG|GR|ERROR|[gracefulRebootNotification][3468] graceful reboot reason : Load_Average_Graceful_Reboot
            [
                [
                    ['^.*\[gracefulRebootNotification\]', 'Graceful Reboot : '],
                ],
                "ERR",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            #Jul 15 11:08:01 powertv syslog: DLOG|GR|ERROR|...
            [
                [
                    ['^.*DLOG\|GR\|ERROR\|', 'Graceful Reboot : '],
                ],
                "WARN",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            #Jul 15 11:08:01 powertv syslog: DLOG|GR|NORMAL|...
            [
                [
                    ['^.*DLOG\|GR\|NORMAL\|', 'Graceful Reboot : '],
                ],
                "INFO",
                "GENERAL"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jul 20 18:02:32 powertv csp_CPERP: DLOG|GALIO|MINOR_DEBUG|package://6EA49453-0A31D450/js/lib/console.js at line 48 [VOD VOD.Swimlane.Collection] [DEBUG] Building asset lane 
            [
                [
                    ['^.*Building asset lane', 'Building asset lane']
                ],
                "INFO",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jul 21 20:35:23 powertv syslog: DLOG|GALIO|MINOR_DEBUG|package://B1C1C033-0FFBB093/js/lib/console.js at line 48 [VOD VOD.Swimlane.Manager] [DEBUG] Reset Swimlane posters
            [
                [
                    ['^.*Reset Swimlane posters', 'Reset Swimlane posters']
                ],
                "INFO",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jul 21 20:35:25 powertv syslog: DLOG|GALIO|MINOR_DEBUG|package://B1C1C033-0FFBB093/js/lib/console.js at line 48 [VOD VOD.Swimlane.Item] [DEBUG] Setting image src for asset -> Eye In The Sky (HD); uid: 33760120; url: file:///tmp/VodArt/de274ae7-fc46-4dc3-8752-f89db7b34fe2.jpg
            [
                [
                    ['^.*Setting image src for asset', 'Setting image src for asset']
                ],
                "INFO",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Jul 21 20:34:59 powertv syslog: DLOG|GALIO|MINOR_DEBUG|package://B1C1C033-0FFBB093/js/lib/console.js at line 48 [VOD VOD.Lib.ApiAsset] [DEBUG] Error loading file:///tmp/VodArt/5d5ab104-15ce-4c33-a9b5-3b6d8ddead85.jpg 
            [
                [
                    ['^.*Error loading file', 'Error loading poster image: ']
                ],
                "WARN",
                "VOD"
            ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Apr  4 18:33:43 powertv syslog: DLOG|MDA|NORMAL|catalogue_vod__update_iterator: list->page_number:50495  requested_page_number:50496
            # [
            #     [
            #         ['^.*catalogue_vod__update_iterator: .*requested_page_number:', 'VOD app requested page number = ']
            #     ],
            #     "INFO",
            #     "VOD"
            # ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
            # Apr  7 10:30:41 powertv syslog: DLOG|GALIO|MINOR_DEBUG|package://C41C1081-E7C1D652/js/lib/console.js at line 74 [VOD VOD.Lib.ApiAssetCache] [DEBUG] Setting next page for asset cache -> root: page: 1
            # [
            #     [
            #         ['^.*VOD .*DEBUG.* Setting next page .* page: ', 'VOD app requested page number = ']
            #     ],
            #     "INFO",
            #     "VOD"
            # ],
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#
        ]
#. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .#

def lineParser( line ):
    '''
    This function is invoked on every line in the log file.
    It attempts to call specific_parser_function if there is one, else it 
    invokes generic regexParser.
    '''

    ret = False
    for parser in parsers:
        try:
            logMode = parser[1]
        except:
            logMode = "INFO"

        try:
            logModule = parser[2]
        except:
            logModule = "GENERAL"
        
        try:
            ret = parser[0](line, logMode, logModule)
        except:
            try:
                ret = regexParser(line, parser[0], logMode, logModule)
            except:
                logIt("ERR: invalid regex provided, skipping it: %s " % line, "FORCE")

        if ret:
            break
    return

#-----------------------------------------------------------------------------#

# main

if __name__ == '__main__':

    ap = argparse.ArgumentParser( formatter_class = argparse.RawTextHelpFormatter, description = parserInfo)
    ap.add_argument( 'log', nargs = '+', help = "normal or compressed(.gz) logs to parse.\n" +
                                                "dir/log1 dir/log2 dir/log3.gz ... dir/logn\n" + 
                                                "dir/log*\n" +
                                                "dir/*")
    ap.add_argument( "-p", "--outPath", nargs = '?', help = "path for storing loghog.out[.html/json]")
    args = ap.parse_args()

    if args.outPath:
        outPath = args.outPath
        outPath = outPath + "/"

    fhtml = open(outPath+loghog+".out.html", "w")
    fhtml.write('<html><body style="background-color:grey; font-family:Tahoma; font-size:14px;">'+'\n')
    fjson = open(outPath+loghog+".out.json", "w")
    fjson.write('['+'\n')

    args.log.sort()
    if (args.log[0] == "slog"):
        args.log.append(args.log.pop(0))
    
    for log in args.log:
        logIt("Processing file : " + log, "FORCE")
        fileName, fileExt = os.path.splitext(log)
        logHighlights = ""

        try:
            if fileExt == ".gz":
                with gzip.open(log, 'r') as f:
                    for lineCount, line in enumerate(f):
                        lineParser(line)
            else:
                with open(log, 'r') as f:
                    for lineCount, line in enumerate(f):
                        lineParser(line)
        except:
            logIt("ERR : invalid log file: " + log, "FORCE")
            logIt(separator, "FORCE")
            continue

    # post process

        if logHighlights:
            logIt(log + " parsed successfully.", "FORCE")
        else:
            logIt("WARN: nothing to parse: " + log, "FORCE")
        logIt(separator, "FORCE")

    fhtml.write('</body></html>')
    fhtml.close()
    fjson.write(']')
    fjson.close()
#-----------------------------------------------------------------------------#