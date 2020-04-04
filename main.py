from L76GNSS import L76GNSS
from machine import RTC
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE
from MicroWebSrv2  import *
from network import WLAN
from pycoproc import Pycoproc
from time          import sleep
from _thread       import allocate_lock


import gc
import machine
import file_ops
import lte_funcs as ltef
import json
import os
import pycom
import socket
import ssl
import sys
import _thread
import time
import utime
import uos


# try:
from pymesh_config import PymeshConfig
# except:
#     from _pymesh_config import PymeshConfig

# try:
from pymesh import Pymesh
# except:
#     from _pymesh import Pymesh

lh_mesh_version = "1.1.4"


# ============================================================================

@WebRoute(GET, '/test-redir')
def RequestTestRedirect(microWebSrv2, request) :
    request.Response.ReturnRedirect('/sd/chat.txt')

# ============================================================================

@WebRoute(GET, '/comms', name='Comms1/2')
def RequestTestPost(microWebSrv2, request) :
    with open('/sd/www/sms.txt', 'r') as f:
        sms_temp = f.read().split('\r\n')
        f.close()

    SMS = [string for string in sms_temp if string != ""]
    print(SMS)
    SMS = SMS[-5:]
    print(SMS)
    try:
        sms1 = SMS[0]
        print("SMS 0: %s" % SMS[0])
    except:
        sms1 = ' '
    try:
        sms2 = SMS[1]
    except:
        sms2 = ' '
    try:
        sms3 = SMS[2]
    except:
        sms3 = ' '
    try:
        sms4 = SMS[3]
    except:
        sms4 = ' '
    try:
        sms5 = SMS[4]
    except:
        sms5 = ' '

    content = """\
    <!DOCTYPE html>
    <html>
        <head>
            <title>Comms 1/2</title>
            <link rel="stylesheet" href="style.css" />
        </head>

        <body>
            <h2>LHVW Comms Page 1/2</h2>
            <br />
            <form action="/comms" method="post">
                Add html for sennding messages to external chat rooms, SMS, <br />
                and for sending webpage scrape requests to BR and LTE<br />
                Will need methods for finding which nodes are BR or LTE<br />
                Then 4 input fields for mac/sms and mac/br_msg (for ext chat)<br />
                %s
                SMS Mac: <input type="text" name="LTEMAC"><br />
                SMS Phone Number: <input type="text" name="SMSNUM"><br />
                SMS Message:  <input type="text" name="SMSMSG"><br />

                <br />
                <input type="submit" value="Submit changes" size="30">
                <br />
                <br />
                Last 5 SMS messages will show if this node has LTE:
                %s<br />
                %s<br />
                %s<br />
                %s<br />
                %s<br />


    </html>
    """ % (NODE_NAME, sms1, sms2, sms3, sms4, sms5)
    request.Response.ReturnOk(content)

# ------------------------------------------------------------------------

@WebRoute(POST, '/comms', name='Comms2/2')
def RequestTestPost(microWebSrv2, request) :
    data = request.GetPostedURLEncodedForm()
    print("This space to send SMS and BR requests")
    if data['SMSNUM'] != 0 and data['SMSMSG'] != 0:
        try:
            lte_funcs.send_sms(data['SMSNUM'], data['SMSMSG'])
        except:
            msg = ("JM send sms %s %s" % (data['SMSNUM'], data['SMSMSG']))
            pymesh.send_mess(data['LTEMAC'], str(msg))
    else:
        print("No message to send")

    content   = """\
    <!DOCTYPE html>
    <html>
        <head>
            <title>Comms 2/2</title>
            <link rel="stylesheet" href="style.css" />
        </head>
        <body>
            <h2>Comms - POST 2/2</h2>
            Need to figure out how to display received SMS or external chat<br />
            PHow to display webpage scrape<br />
            Or how to return error if things don't work.<br />
            <p>
                Go home « <a href="/index.html">Home</a> »
            </p>
        </body>
    </html>
    """
    request.Response.ReturnOk(content)

# ============================================================================

@WebRoute(GET, '/node-config', name='NodeConfig1/2')
def RequestTestPost(microWebSrv2, request) :
    NODE_TIME = utime.localtime()
    content = """\
    <!DOCTYPE html>
    <html>
        <head>
            <title>Node Config 1/2</title>
            <link rel="stylesheet" href="style.css" />
        </head>

        <body>
            <h2>LHVW Chat Node Configuration 1/2</h2>
            User address: %s<br />
            <form action="/node-config" method="post">
                WIFI SSID: <input type="text" value=%s name="SSID"><br />
                WIFI Password:  <input type="text" value=%s name="PASS"><br />
                Node Mac:  <input type="text" value=%s name="MAC"><br />
                <br />
                <br />
                If any of the values below are changed, they need to be changed <br />
                on every node in the mesh or else the mesh won't connect.<br />
                Tread cautiously, but this is how you make your mesh 'unique'.<br />

                Node Name:  <input type="text" value=%s name="NODENAME"><br />
                Mesh Frequency:  <input type="text" value=%s name="FREQ"><br />
                From 902000000 to 915000000, default is 904600000<br />
                Mesh bandwidth:  <input type="text" value=%s name="BAND"><br />
                LoRa.BW_125KHZ is "0"<br />
                LoRa.BW_250KHZ is "1"<br />
                LoRa.BW_500KHZ is "2"<br />
                Spreading Factor:  <input type="text" value=%s name="SPRDFACT"><br />
                7 is fastest, 12 is slow with longer range<br />
                Mesh Key:  <input type="text" value=%s name="MESHKEY"><br />
                112233<br />
                <br />
                <br />
                Double check everything before you click submit<br />
                A really fubar entry will lock up the node and require a hard rest<br />
                Error checking eventually.
                <br />
                <input type="submit" value="Submit changes" size="30">
                <br />
                <br />
                Current node RTC time:<br />
                %s<br />
                <input id="DTIME" type="text" name="TIME" size="50"><br />
                <br />
                <br />


            </form>
        </body>

        <script language="javascript">
        var dyear = new Date().getFullYear();
        var dtempmonth = new Date().getMonth();
        var dmonth = dtempmonth + 1;
        var ddate = new Date().getDate();
        var dhours = new Date().getHours();
        var dminutes = new Date().getMinutes();
        var all_time = "(" + dyear.toString() + ", " + dmonth.toString() + ", " + ddate.toString() + ", " + dhours.toString() + ", " + dminutes.toString() + ", 00, 00, 00)";
        var all_timeJSON = JSON.stringify(all_time);
        document.getElementById("DTIME").value = all_timeJSON;
        </script>

    </html>
    """ % (request.UserAddress[0], NODE_SSID, NODE_PASS, NODE_MAC, NODE_NAME, MESH_FREQ, MESH_BAND, MESH_SPRED, MESH_KEY, NODE_TIME)
    request.Response.ReturnOk(content)

# ------------------------------------------------------------------------

@WebRoute(POST, '/node-config', name='NodeConfig2/2')
def RequestTestPost(microWebSrv2, request) :
    data = request.GetPostedURLEncodedForm()
    try :
        ssid = data['SSID']
        passwrd = data['PASS']
        mac = data['MAC']
        node_name = data['NODENAME']
        mesh_freq = data['FREQ']
        mesh_band = data['BAND']
        spread_fact = data['SPRDFACT']
        mesh_key = data['MESHKEY']
        device_time = data['TIME']

        print(device_time)
        print(type(device_time))

        set_js_time(device_time)

        node_dict = {
        'WIFI_SSID': str(ssid),
        'WIFI_PASS': str(passwrd),
        'NODE_MAC':  str(mac),
        'NODE_NAME': str(node_name),
        'MESH_FREQ': str(mesh_freq),
        'MESH_BAND': str(mesh_band),
        'SPREAD_FACT': str(spread_fact),
        'MESH_KEY': str(mesh_key)
        }

    except :
        request.Response.ReturnBadRequest()
        return
    try:
        with open('/sd/www/node_config.txt', 'w') as f:
            for key in node_dict:
                f.write("%s, %s" % (key, node_dict[key]))
                f.write('\r\n')
            f.close()
    except:
        print("Failed")

    try:
        write_json_config_file(mac, mesh_freq, mesh_band, spread_fact, mesh_key)
        print("written")
    except:
        print("Not writing json")

    content   = """\
    <!DOCTYPE html>
    <html>
        <head>
            <title>POST 2/2</title>
            <link rel="stylesheet" href="style.css" />
        </head>
        <body>
            <h2>MicroWebSrv2 - POST 2/2</h2>
            Node config has been set<br />
            Power Cycle Node for settings to take effect<br />
            Or go back to home to redo settings if you made a mistake <br />
            <p>
                Go home « <a href="/index.html">Home</a> »
            </p>
        </body>
    </html>
    """
    request.Response.ReturnOk(content)



# ============================================================================
# ============================================================================

@WebRoute(GET, '/node-diag', name='NodeDiag1/2')
def RequestTestPost(microWebSrv2, request) :
    NODE_STATE = pymesh.status_str()
    try:
        HTML_LEADER = leader
        NODE_MML_LEN = len(RECEIVED_MAC_LIST)
        NODE_MML = RECEIVED_MAC_LIST
        # leader = find_leader()
    except:
        HTML_LEADER = "No Leader currently"
        NODE_MML_LEN = "No Mesh list, not received from leader"
        NODE_MML = "No Mesh list, not received from leader"

    content = """\
    <!DOCTYPE html>
    <html>
        <head>
            <title>Node Diagnostic 1/2</title>
            <link rel="stylesheet" href="style.css" />
        </head>
        <body>
            <h2>LHVW Chat Node Diagnostic 1/2</h2>
            <form action="/node-diag" method="post">
                Node's current state:<br />
                %s <br />
                <br />
                Typically will be Role 3 (router) or Role 4 (leader), <br />
                Role 0 (deattached) or Role 1 (single leader) implies a problem with the mesh.<br />
                Power cycle the node after a couple minutes.<br />
                <br />
                Mac address of this node. Use this for the direct message commands below: %s. <br />
                <br />
                Number of nodes connected to mesh: %s. <br />
                <br />
                List of node mac addresses: <br >
                %s <br />
                <br />
                If the two lines above say "No mesh list" send the "JM send mml 'my_mac'" command below to the leader.<br />
                <br />
                <br />
                Leader Mac address: %s <br />
                <br />
                <br />
                Node mac address for sending a direct message: <br />
                <input type="text" name="N_MAC" size="50"><br />
                Message for node: <br />
                <input type="text" name="N_MSG" size="100"><br />
                <br />
                <input type="submit" value="Send Message" size="30">

                <h2>"JM Messages"</h2>
                A series of commands that can be sent to nodes for more info.<br />
                Use the address on the "my mac address" line above as the "my_mac" below.
                <ul>
                    <li>"JM send self 'my mac'"</li>
                    <li>This request the self info a node, role, signal strength, neighbors, etc</li>
                    <br />
                    <li>"JM set time (2020, 3, 27, 10, 53, 00, 00, 00) 'my mac'"</li>
                    <li>This will tell a node to sync it's RTC to the time sent.<br />
                    It requires a very specific format or else won't work <br />
                    "JM set time (year, month, date, hour, minutes, 00, 00, 00) 'my_mac'"<br />
                    "hours" are in 24 hour clock format, 7pm is '19' </li>
                    <br />
                    <li>"JM how set 'my mac'"</li>
                    <li>Will ask a node what it's clock is set to</li>
                    <br />
                    <li>"JM send name 'my mac'"</li>
                    <li>Asks a node to send it's 'name' if it has one. <br />
                     Makes it easier to know which node/perso to send messages to.n</li>
                     <br />
                    <li>"JM RESET"</li >
                    <li>Reboots remote node.</li>
                    <br />
                    <li>"JM set my time 'my mac'"</li>
                    <li>"JM set your time"</li>
                    <li>The two above command either your node or a remote node to<br />
                    message the node with Mac address "1" and request it update their time.<br />
                    This only works if take a easily accessible node, change the mac to 1,<br />
                    and keep the time constantly updated on it.</li>
                    <br />
                    <li>"JM send mml 'my mac'"</li>
                    <li>Requests the leader to send the lastest list of the nodes on the<br />
                    mesh's macs</li>
                    <br />
                    <li>"JM add me 'my mac'"</li>
                    <li>Sends your mac to the leader node to be added to the mml, <br />
                    in case it didn't happen automagically.</li>
                    <br />
                    <li>"JM how set 'my mac'"</li>
                    <li>Will ask a node what it's clock is set to</li>
                    <br />
                    <li>"JM send svw 'my mac'"</li>
                    <li>Request software version of a node.</li>
                    <br />
                    <li>The next set of messages can be sent to any node, but<br />
                    not all of the nodes have the sensors to send back the data.</li>
                    <br />
                    <li>"JM batt level 'my mac'"</li>
                    <li>Battery level</li>
                    <br />
                    <li>"JM send GPS 'my mac'"</li>
                    <li>GPS</li>
                    <br />
                    <li>"JM send temp 'my mac'"</li>
                    <li>Sends temperature inside the enclosure.</li>
                    <br />
                    <li>"JM send baro 'my mac'"</li>
                    <li>Sends barometric pressure, usually moot if it's in a <br />
                    container.</li>
                </ul>
                <p>
                    Go home « <a href="/index.html">Home</a> »
                </p>
            </form>
        </body>
    </html>
    """ % (NODE_STATE, NODE_MAC, NODE_MML_LEN, NODE_MML, HTML_LEADER)
    request.Response.ReturnOk(content)

# ------------------------------------------------------------------------

@WebRoute(POST, '/node-diag', name='NodeDiag2/2')
def RequestTestPost(microWebSrv2, request) :
    data = request.GetPostedURLEncodedForm()
    try :
        print("sending msg")
        if data['N_MAC'] != 0 and data['N_MSG'] != 0:
            status_msg = ("Sending message ''%s' to %s mac, check status or ack log for response." % (data['N_MAC'], data['N_MSG']))
            with _chatLock:
                time.sleep(1)
                pymesh.send_mess(str(data['N_MAC']), str(data['N_MSG']))
                time.sleep(1)
        else:
            status_msg = "Nothing to send"
    except:
        print("Something went wrong in msg format")

    content   = """\
    <!DOCTYPE html>
    <html>
        <head>
            <title>POST Diagnostic 2/2</title>
            <link rel="stylesheet" href="style.css" />
        </head>
        <body>
            <h2>MicroWebSrv2 - POST 2/2</h2>
            %s<br />
            <p>
                Go back to send another message « <a href="/node-diag">Node Diagnostic</a> »
            </p>
            <p>
                Go back to the status log and refresh to see response: « <a href="/status_log.txt">Status Log</a> »
            </p>
            <p>
                Or go to the ack log and refresh to see if message was received: « <a href="/status_log.txt">Status Log</a> »
            </p>
            Or go back to home if done <br />
            <p>
                Go home « <a href="/index.html">Home</a> »
            </p>
        </body>
    </html>
    """ % (status_msg)
    request.Response.ReturnOk(content)



# ============================================================================


def OnWebSocketAccepted(microWebSrv2, webSocket) :
    print('Example WebSocket accepted:')
    print('   - User   : %s:%s' % webSocket.Request.UserAddress)
    print('   - Path   : %s'    % webSocket.Request.Path)
    print('   - Origin : %s'    % webSocket.Request.Origin)
    print("send node to leader")
    send_leader_hi(leader)
    my_mac = pymesh.mesh.mesh.MAC
    if my_mac == leader:
        macs = leader_gets_own_mesh_macs()
    else:
        ask_for_mesh_macs(leader)
    if webSocket.Request.Path.lower() == '/wschat' :
        WSJoinChat(webSocket)
    else :
        webSocket.OnTextMessage   = OnWebSocketTextMsg
        webSocket.OnBinaryMessage = OnWebSocketBinaryMsg
        webSocket.OnClosed        = OnWebSocketClosed

# ============================================================================
# ============================================================================
# ============================================================================

def OnWebSocketTextMsg(webSocket, msg) :
    print('WebSocket text message: %s' % msg)
    webSocket.SendTextMessage('Received "%s"' % msg)

# ------------------------------------------------------------------------

def OnWebSocketBinaryMsg(webSocket, msg) :
    print('WebSocket binary message: %s' % msg)

# ------------------------------------------------------------------------

def OnWebSocketClosed(webSocket) :
    print('WebSocket %s:%s closed' % webSocket.Request.UserAddress)

# ============================================================================
# ============================================================================
# ============================================================================

global _chatWebSockets
_chatWebSockets = [ ]

global _chatLock
_chatLock = allocate_lock()

# ------------------------------------------------------------------------

def WSJoinChat(webSocket) :
    gc.collect()
    print("Current available memory after chat join: %d" % gc.mem_free())
    webSocket.OnTextMessage = OnWSChatTextMsg
    webSocket.OnClosed      = OnWSChatClosed
    addr = webSocket.Request.UserAddress
    my_mac = pymesh.mesh.mesh.MAC
    print("Ask leader for mac list")
    if my_mac == leader:
        macs = leader_gets_own_mesh_macs()
    else:
        try:
            macs = RECEIVED_MAC_LIST
        except:
            time.sleep(1)
            ask_for_mesh_macs(leader)
            time.sleep(1)
            try:
                macs = RECEIVED_MAC_LIST
            except:
                print("somethings locked up")
                with _chatLock :
                    webSocket.SendTextMessage('No nodes have joined chat, wait and refresh page')

    print("The current macs are %s" % macs)
    msg1 = make_message_status(('A user from %s has joined>' % NODE_NAME))
    msg_update = last_10_messages()
    with _chatLock :
        for ws in _chatWebSockets :
            gc.collect()
        _chatWebSockets.append(webSocket)
        for i in range(len(msg_update)-1):
            webSocket.SendTextMessage('Previous MSG: %s' % msg_update[i])
            gc.collect()
        # pymesh.send_mess('ff03::1', msg1)
        # pymesh.send_mess('ff03::1', msg2)
        for mac in macs:
            if mac == my_mac:
                print("skip")
            else:
                print(mac)
                pymesh.send_mess(mac, msg1)
                gc.collect()
                time.sleep(1)
    print("Current available memory after chat join: %d" % gc.mem_free())

# ------------------------------------------------------------------------

def OnWSChatTextMsg(webSocket, msg) :
    gc.collect()
    send_leader_hi(leader)
    my_mac = pymesh.mesh.mesh.MAC
    time.sleep(1)
    if my_mac == leader:
        print("Will get macs from file")
    else:
        ask_for_mesh_macs(leader)
    time.sleep(1)
    addr = webSocket.Request.UserAddress
    if my_mac == leader:
        macs = leader_gets_own_mesh_macs()
    else:
        try:
            macs = RECEIVED_MAC_LIST
        except:
            time.sleep(1)
            ask_for_mesh_macs(leader)
            time.sleep(1)
            try:
                macs = RECEIVED_MAC_LIST
            except:
                print("somethings locked up")
                with _chatLock :
                    webSocket.SendTextMessage('No nodes have joined chat, wait and refresh page')
    len_mac = (len(macs)-1)
    now_time = current_time()
    with _chatLock :
        for ws in _chatWebSockets :
            self_node_msg = ("Sent to %s nodes: %s" % (len_mac, msg))
            ws.SendTextMessage(str(self_node_msg))
            gc.collect()
        # pymesh.send_mess('ff03::1', new_msg)
        for mac in macs:
            print(macs)
            if mac == my_mac:
                print("skip")
            else:
                pymesh.send_mess(mac, str(msg))
                gc.collect()
                time.sleep(1)
    f = open('/sd/www/chat.txt', 'a+')
    f.write('%s %s\n' % (now_time, msg))
    f.close()
    print('Wrote msg to SD, chat.txt')
    print("Current available memory after text sent: %d" % gc.mem_free())
# ------------------------------------------------------------------------

def OnWSChatClosed(webSocket) :
    gc.collect()
    addr = webSocket.Request.UserAddress
    my_mac = pymesh.mesh.mesh.MAC
    try:
        macs = RECEIVED_MAC_LIST
    except:
        time.sleep(1)
        ask_for_mesh_macs(leader)
        time.sleep(1)
        try:
            macs = RECEIVED_MAC_LIST
        except:
            print("somethings locked up")
    msg1 = make_message_status(('<User HAS LEFT THE CHAT>'))
    pycom.rgbled(0x000A00)
    with _chatLock :
        if webSocket in _chatWebSockets :
            _chatWebSockets.remove(webSocket)
            for ws in _chatWebSockets :
                ws.SendTextMessage(msg1)
                gc.collect()
        # pymesh.send_mess('ff03::1', msg1)
        # for mac in macs:
        #     if mac == my_mac:
        #         continue
        #     else:
        #         pymesh.send_mess(mac, msg1)
        #         gc.collect()
        #         time.sleep(1)
    print("Current available memory after chat exit: %d" % gc.mem_free())

def OnMWS2Logging(microWebSrv2, msg, msgType) :
    print('Log from custom function: %s' % msg)

# ============================================================================
# ============================================================================
# ============================================================================

print()

def set_js_time(jtime):
    time_from_jtime = jtime[2:-2]
    jtime_from_message_tuple = tuple(map(int, time_from_jtime.split(", ")))
    rtc.init(jtime_from_message_tuple)
    print("Time set")

def last_10_messages():
    with open('/sd/www/chat.txt', 'r') as f:
        all_messages = f.read().split('\n')
        f.close()
    last_messages = all_messages[-11:]
    return last_messages

def write_json_config_file(mac, freq, band, sprd, key):
    json_config = ('{"ble_api": false, "autostart": true, "ble_name_prefix": "PyGo ", "debug": 5, "LoRa": {"sf": %s, "region": 8, "freq": %s, "bandwidth": %s, "tx_power": 14}, "MAC": %s, "Pymesh": {"key": "%s"}}' % (sprd, freq, band, mac, key))
    try:
        with open('/sd/www/pymesh_config.json', 'w+') as f:
            f.write(str(json_config))
            f.close()
    except:
        print("File didn't write")

def create_node_config_dict():
    node_config_dict = {}
    try:
        with open('/sd/www/node_config.txt') as f:
            node_config_list_from_file = f.read().split('\r\n')
            f.close()
    except:
        with open('/node_config.txt') as f:
            node_config_list_from_file = f.read().split('\r\n')
            f.close()
    node_config_list = node_config_list_from_file[:8]
    for i in range(len(node_config_list)):
        temp_list = list(node_config_list[i].split(', '))
        node_config_dict[temp_list[0]] = temp_list[1]
    return node_config_dict

def sending_gps(sending_mac):
    if pytrack_s == True:
        coord = l76.coordinates()
        msg = make_message_status(str(coord))
        time.sleep(1)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)
    elif pytrack_s == False:
        no_gps = "This node doesn't have GPS"
        msg = make_message_status(no_gps)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

def send_baro(sending_mac):
    if pysense_s == True:
        if len(sending_mac) == 0:
            print("Mac address format wrong")
            return
        msg1 = make_message_status(("MPL3115A2 temperature: " + str(mp.temperature())+
                " Altitude: " + str(mp.altitude())))
        pymesh.send_mess(sending_mac, str(msg1))
        time.sleep(1)
    elif pysense_s == False:
        no_baro = "This node doesn't have Baro"
        msg = make_message_status(no_baro)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

def send_temp(sending_mac):
    if pysense_s == True:
        if len(sending_mac) == 0:
            print("Mac address format wrong")
            return
        msg1 = make_message_status(("Temperature: " + str(si.temperature())+
                " deg C and Relative Humidity: " + str(si.humidity()) + " %RH"))
        pymesh.send_mess(sending_mac, str(msg1))
        time.sleep(1)
    elif pysense_s == False:
        no_temp = "This node doesn't have Temp"
        msg = make_message_status(no_temp)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

def send_mesh_version(sending_mac):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
        return
    msg = make_message_status(("Node SW version: %s" % lh_mesh_version))
    time.sleep(1)
    with _chatLock :
        for ws in _chatWebSockets :
                ws.SendTextMessage(msg)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

def make_message_status(msg):
    status_msg = ("STATUS: %s" % msg)
    return status_msg

def format_time(given_time):
    format_time = ("[%d:%d %d/%d]"  % (given_time[3], given_time[4], given_time[1], given_time[2]))
    return format_time

def current_time():
    current_time = utime.localtime()
    formatted_time = format_time(current_time)
    return formatted_time

def set_time(sending_mac, msg):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
        return
    time_from_message_string = msg[16:-1]
    print(time_from_message_string)
    time_from_message_tuple = tuple(map(int, time_from_message_string.split(", ")))
    rtc.init(time_from_message_tuple)
    msg = make_message_status("Time Set")
    time.sleep(1)
    with _chatLock :
        for ws in _chatWebSockets :
                ws.SendTextMessage(msg)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

def first_time_set():
    current_time = utime.localtime()
    if current_time[0] == 1970:
        print("Time's wrong, send request to fix")
        wake = make_message_status("wake up 1!")
        time.sleep(1)
        pymesh.send_mess(1, str(wake))
        time.sleep(1)
        msg = ("JM set my time %s" % str(mac))
        pymesh.send_mess(1, str(msg))
        time.sleep(1)
    else:
        print("Time is correct")

def set_my_time(sending_mac):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
    else:
        now_time = utime.localtime()
        msg = ("JM set time 01 %s" % str(now_time))
        time.sleep(1)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

def how_time_set(sending_mac):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
    else:
        now_time = current_time()
        msg = make_message_status(("Current:" + now_time + " Else, (year, month, day, hours, minutes, seconds, micros, timezone)"))
        time.sleep(1)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

def pop_mesh_pairs_list():
    mps = pymesh.mesh.get_mesh_pairs()
    if len(mps) == 0:
        time.sleep(5)
        mps = pymesh.mesh.get_mesh_pairs()
        if len(mps) == 0:
            time.sleep(5)
            mps = pymesh.mesh.get_mesh_pairs()
        else:
            return mps
    else:
        return mps

def find_leader():
    node_state = pymesh.status_str()
    print("Node state : %s" % str(node_state))
    my_mac = str(pymesh.mesh.mesh.MAC)
    mesh_mac_list = pymesh.mesh.get_mesh_mac_list()
    if node_state[:6] == 'Role 4':
        leader_mac = my_mac
    elif len(mesh_mac_list) == 2:
        leader_mac = mesh_mac_list.remove(my_mac)
    else:
        mps = pop_mesh_pairs_list()
        try:
            leader_mac = mps[0][1]
        except:
            leader_mac = NODE_MAC
    return leader_mac

def send_battery_voltage(sending_mac):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
        return
    try:
        volts = str(py.read_battery_voltage())
        own_mac = str(pymesh.mesh.mesh.MAC)
        msg = make_message_status(('Mac Address %s battery level is: %s' % (own_mac, volts)))
        time.sleep(1)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)
    except:
        if exp31 == True:
            msg = make_message_status("No ADC")
            with _chatLock :
                for ws in _chatWebSockets :
                        ws.SendTextMessage(msg)
                pymesh.send_mess(sending_mac, str(msg))
                time.sleep(1)

def send_self_info(sending_mac):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
        return
    node_info = str(pymesh.mesh.get_node_info())
    msg = make_message_status(("self info: %s" % node_info))
    time.sleep(1)
    with _chatLock :
        for ws in _chatWebSockets :
                ws.SendTextMessage(msg)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

def send_leader_hi(leader):
    my_mac = str(pymesh.mesh.mesh.MAC)
    if my_mac == leader:
        print("Either this node is the leader or not connected to mesh, not saying hi")
    else:
        msg = ("JM add me %s" % my_mac)
        with _chatLock :
            pymesh.send_mess(leader, str(msg))
            time.sleep(1)


def add_me_leader(sending_mac):
    print("Adding to mesh leader mac list")
    msg = make_message_status("Node Added")
    with open('/sd/www/leader_mesh_list.txt') as f:
        temp_mac_list = f.read().split('\r\n')
        f.close()
    if (sending_mac in temp_mac_list):
        print("Node already in list")
        with _chatLock :
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)
    else:
        with open('/sd/www/leader_mesh_list.txt', 'a') as f:
            f.write(sending_mac)
            f.write('\r\n')
            f.close()
        with _chatLock :
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

def leader_gets_own_mesh_macs():
    my_mac = str(pymesh.mesh.mesh.MAC)
    with open('/sd/www/leader_mesh_list.txt') as f:
        temp_mac_list = f.read().split('\r\n')
        f.close()
    mac_list = list( dict.fromkeys(temp_mac_list[:-1]) )
    mac_list.append(my_mac)
    return mac_list

def ask_for_mesh_macs(leader):
    my_mac = str(pymesh.mesh.mesh.MAC)
    msg = ("JM send mml %s" % my_mac)
    with _chatLock :
        pymesh.send_mess(leader, str(msg))
        time.sleep(1)
    time.sleep(1)

def send_back_mml(sending_mac):
    my_mac = str(pymesh.mesh.mesh.MAC)
    temp_mac_list = []
    with open('/sd/www/leader_mesh_list.txt') as f:
        temp_mac_list = f.read().split('\r\n')
        f.close()
    mac_list = list( dict.fromkeys(temp_mac_list[:-1]) )
    mac_list.append(my_mac)
    msg = ("JM receive mml %s" % str(mac_list))
    with _chatLock :
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

def save_mml(msg):
    mac_string = msg[1:-1]
    # temp_mac_list = mac_string.split(", ")
    temp_string = mac_string.strip("'")
    temp_mac_list = temp_string.split("', '")
    mac_list = []
    mac_list = [int(i) for i in temp_mac_list]
    return mac_list

def send_name(sending_mac):
    with _chatLock :
        pymesh.send_mess(sending_mac, str(NODE_NAME))
        time.sleep(1)

def new_message_cb(rcv_ip, rcv_port, rcv_data):
    ''' callback triggered when a new packet arrived '''
    print('Incoming %d bytes from %s (port %d):' %
            (len(rcv_data), rcv_ip, rcv_port))
    now_time = current_time()
    msg = rcv_data.decode("utf-8")
    if msg[:6] == "STATUS":
        f = open('/sd/www/status_log.txt', 'a+')
        f.write('%s %s\n' % (now_time, msg))
        f.close()
        print('Wrote status msg to log')

    elif msg[:2] == "JM":
        if msg[:13] == "JM batt level":
            sending_mac = msg[14:]
            send_battery_voltage(sending_mac)
        elif msg[:12] == "JM send self":
            sending_mac = msg[13:]
            send_self_info(sending_mac)
        elif msg[:8] == "JM RESET":
            machine.reset()
        elif msg[:11] == "JM set time":
            sending_mac = msg[12:14]
            set_time(sending_mac, msg)
        elif msg[:10] == "JM how set":
            sending_mac = msg[11:]
            how_time_set(sending_mac)
        elif msg[:11] == "JM send GPS":
            sending_mac = msg[12:]
            sending_gps(sending_mac)
        elif msg[:12] == "JM send baro":
            sending_mac = msg[13:]
            send_baro(sending_mac)
        elif msg[:12] == "JM send temp":
            sending_mac = msg[13:]
            send_temp(sending_mac)
        elif msg[:14] == "JM set my time":
            sending_mac = msg[15:]
            set_my_time(sending_mac)
        elif msg[:16] == "JM set your time":
            first_time_set()
        elif msg[:11] == "JM send swv":
            sending_mac = msg[12:]
            send_mesh_version(sending_mac)
        elif msg[:9] == "JM add me":
            sending_mac = msg[10:]
            add_me_leader(sending_mac)
        elif msg[:11] == "JM send mml":
            sending_mac = msg[12:]
            send_back_mml(sending_mac)
        elif msg[:14] == "JM receive mml":
            msg = msg[15:]
            global RECEIVED_MAC_LIST
            RECEIVED_MAC_LIST = save_mml(msg)
        elif msg[:12] == "JM send name":
            sending_mac = msg[13:]
            send_name(sending_mac)
        elif msg[:11] == "JM send sms":
            sen_to_number = msg[12:23] #JM send sms 15084103870 Yo dude are we there yet?
            print(sen_to_number)
            sms_msg = msg[24:]
            print(sms_msg)
            try:
                print("Sending SMS")
                lte_comms.send_sms(sen_to_number, sms_msg)
            except:
                print("No LTE")
        elif msg[:11] == "JM send csq":
            sending_mac = msg[12:]
            lte_comms.signal_strength()
        elif msg[:11] == "JM read sms":
            sending_mac = msg[12:]
            lte_comms.check_read_sms()


    else:
        with _chatLock :
            for ws in _chatWebSockets :
                ws.SendTextMessage('%s' % (msg))

        f = open('/sd/www/chat.txt', 'a+')
        f.write('%s %s\n' % (now_time, msg))
        f.close()
        print('Wrote msg to SD, chat.txt')
        for _ in range(5):
            pycom.rgbled(0x888888)
            time.sleep(.2)
            pycom.rgbled(0)
            time.sleep(.1)
        pycom.rgbled(0x000066)

    return
gc.enable()
print("Current available memory: %d" % gc.mem_free())
pycom.heartbeat(False)


file_ops.sd_setup()

# read config file, or set default values

node_dict = create_node_config_dict()

NODE_SSID = node_dict['WIFI_SSID']
NODE_PASS = node_dict['WIFI_PASS']
NODE_NAME = node_dict['NODE_NAME']
MESH_FREQ = node_dict['MESH_FREQ']
MESH_BAND = node_dict['MESH_BAND']
MESH_SPRED = node_dict['SPREAD_FACT']
MESH_KEY = node_dict['MESH_KEY']

pymesh_config = PymeshConfig.read_config()


#initialize Pymesh
pymesh = Pymesh(pymesh_config, new_message_cb)
try:
    py = Pycoproc()
except:
    exp31 = True
rtc = RTC()
try:
    l76 = L76GNSS(py, timeout=30)
    pytrack_s = True
    print("Pytrack")
except:
    pytrack_s = False

try:
    si = SI7006A20(py)
    mp = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters. Mode may also be set to PRESSURE, returning a value in Pascals
    mpp = MPL3115A2(py,mode=PRESSURE) # Returns pressure in Pa. Mode may also be set to ALTITUDE, returning a value in meters
    pysense_s = True
    print("Pysense")
except:
    pysense_s = False

if pysense_s == False and pytrack_s == False:
    print("EXP 3.1")

mac = pymesh.mac()

node_dict['NODE_MAC'] = mac
NODE_MAC = node_dict['NODE_MAC']
# if mac > 10:
#     pymesh.end_device(True)
# if mac == 20:
#      pymesh.leader_priority(255)
# elif mac == 15:
#      pymesh.leader_priority(250)

while not pymesh.is_connected():
    print(pymesh.status_str())
    time.sleep(3)

print("Current available memory after pymesh load: %d" % gc.mem_free())
gc.collect()

wlan= WLAN()
wlan.deinit()
wlan = WLAN(mode=WLAN.AP, ssid=NODE_SSID, auth=(WLAN.WPA2, NODE_PASS), channel=11, antenna=WLAN.INT_ANT)
wlan.ifconfig(id=1, config=('192.168.1.1', '255.255.255.0', '192.168.1.1', '8.8.8.8'))

print("AP setting up");


if uos.uname().sysname == 'FiPy':
    try:
        lte_comms = ltef.LteComms()
        print("LTE communication being setup")
        time.sleep(5)
    except:
        print('still broken')

    try:
        print("Attaching LTE to network")
        _thread.start_new_thread(lte_comms.attach_LTE, ())
    except:
        print("Not a fipy")

    # try:
    #     lte_comms.send_sms(19254876005, "From Jamie: A new day a new test.")
    # except:
    #     print("sending sms broke")

    try:
        print("Starting to monitor for new SMS in 60 seconds")
        _thread.start_new_thread(lte_comms.receive_and_forward_to_chat, ())
    except:
        print("retreiving text messages broke")

    # try:
    #     _thread.start_new_thread(lte_comms.connect_lte_data, ())
    #     time.sleep(20)
    # except:
    #     print("Couldn't connect to LTE data")

    # try:
    #     lte_comms.scrape_webpage('www.google.com')
    # except:
    #     print("webpage scrape failed")

    # try:
    #     lte_comms.disconnect_LTE()
    # except:
    #     print("Couldn't disconnect from LTE")
    #
    # try:
    #     lte_comms.unattach_lte()
    # except:
    #     print("Couldn't disconnect from LTE")
else:
    print("Not a fipy")

first_time_set()
pycom.rgbled(0x000A00)
gc.collect()
# Loads the WebSockets module globally and configure it,
wsMod = MicroWebSrv2.LoadModule('WebSockets')
wsMod.OnWebSocketAccepted = OnWebSocketAccepted

# Instanciates the MicroWebSrv2 class,
mws2 = MicroWebSrv2()
mws2.BindAddress = ('192.168.1.1', 80)
mws2.RootPath = '/sd/www'

# For embedded MicroPython, use a very light configuration,
mws2.SetEmbeddedConfig()
mws2.OnLogging = OnMWS2Logging

# All pages not found will be redirected to the home '/',
mws2.NotFoundURL = '/'

# Starts the server as easily as possible in managed mode,
mws2.StartManaged()
node_state = pymesh.status_str()
print("Node state : %s" % str(node_state))
leader = find_leader()
print("Current available memory after wifi ap loads: %d" % gc.mem_free())

def wake_up_leader_to_add():
    if mac != leader:
        send_leader_hi(leader)
        time.sleep(4)
        send_leader_hi(leader)

gc.collect()
# _thread.start_new_thread(wake_up_leader_to_add, ())
wake_up_leader_to_add()

# Main program loop until keyboard interrupt,
try :
    while mws2.IsRunning :
        sleep(1)
except KeyboardInterrupt :
    pass

# End,
print()
mws2.Stop()
print('Bye')
print()

# ============================================================================
# ============================================================================
# ============================================================================
