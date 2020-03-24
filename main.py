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
try:
    from network import LTE
    has_LTE = True
except:
    has_LTE = False
    print("Not a FIPY")

# try:
from pymesh import Pymesh
# except:
#     from _pymesh import Pymesh

lh_mesh_version = "1.1.0"


# ============================================================================

@WebRoute(GET, '/test-redir')
def RequestTestRedirect(microWebSrv2, request) :
    request.Response.ReturnRedirect('/sd/chat.txt')

# ============================================================================

@WebRoute(GET, '/node-config', name='NodeConfig1/2')
def RequestTestPost(microWebSrv2, request) :
    content = """\
    <!DOCTYPE html>
    <html>
        <head>
            <title>Node Config 1/2</title>
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

                <input type="submit" value="OK">
            </form>
        </body>
    </html>
    """ % (request.UserAddress[0], NODE_SSID, NODE_PASS, NODE_MAC, NODE_NAME, MESH_FREQ, MESH_BAND, MESH_SPRED, MESH_KEY)
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
        </head>
        <body>
            <h2>MicroWebSrv2 - POST 2/2</h2>
            Node config has been set<br />
            Power Cycle Node for settings to take effect<br />
            Or go back to home to redo settings if you made a mistake <br />
        </body>
    </html>
    """
    request.Response.ReturnOk(content)



# ============================================================================

def OnWebSocketAccepted(microWebSrv2, webSocket) :
    print('Example WebSocket accepted:')
    print('   - User   : %s:%s' % webSocket.Request.UserAddress)
    print('   - Path   : %s'    % webSocket.Request.Path)
    print('   - Origin : %s'    % webSocket.Request.Origin)
    print("send node to leader")
    send_leader_hi(leader)
    ask_for_mesh_macs(leader)
    # _thread.start_new_thread(first_time_set, ())
    # first_time_set()
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
    try:
        macs = RECEIVED_MAC_LIST
    except:
        time.sleep(5)
        ask_for_mesh_macs(leader)
        time.sleep(5)
        try:
            macs = RECEIVED_MAC_LIST
        except:
            print("somethings locked up")

    print("The current macs are %s" % macs)
    # houses_string = pop_mac_list()
    # house = mac_to_house(my_mac)
    msg1 = make_message_status(('A user has joined>'))
    # msg2 = ("List of current %s" % houses_string)
    msg_update = last_10_messages()
    with _chatLock :
        for ws in _chatWebSockets :
            # ws.SendTextMessage('<%s HAS JOINED THE CHAT>' % house)
            gc.collect()
            # ws.SendTextMessage("List of current %s" % houses_string)
        _chatWebSockets.append(webSocket)
        # house = mac_to_house(my_mac)
        # webSocket.SendTextMessage('<WELCOME %s>' % house)
        # webSocket.SendTextMessage("List of current %s" % houses_string)
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
                time.sleep(1.5)
                # pymesh.send_mess(mac, msg2)
                # time.sleep(1.5)
    print("Current available memory after chat join: %d" % gc.mem_free())

# ------------------------------------------------------------------------

def OnWSChatTextMsg(webSocket, msg) :
    gc.collect()
    addr = webSocket.Request.UserAddress
    my_mac = pymesh.mesh.mesh.MAC
    try:
        macs = RECEIVED_MAC_LIST
    except:
        time.sleep(5)
        ask_for_mesh_macs(leader)
        time.sleep(5)
        try:
            macs = RECEIVED_MAC_LIST
        except:
            print("somethings locked up")
    # new_msg = ('%s: %s' % (str(house), msg))
    now_time = current_time()
    with _chatLock :
        for ws in _chatWebSockets :
            #ws.SendTextMessage(': %s' % new_msg)
            ws.SendTextMessage(str(msg))
            gc.collect()
        # pymesh.send_mess('ff03::1', new_msg)
        for mac in macs:
            if mac == my_mac:
                continue
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
    # macs = get_macs_for_mess()
    my_mac = pymesh.mesh.mesh.MAC
    # house = mac_to_house(my_mac)
    try:
        macs = RECEIVED_MAC_LIST
    except:
        time.sleep(5)
        ask_for_mesh_macs(leader)
        time.sleep(5)
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
        for mac in macs:
            if mac == my_mac:
                continue
            else:
                pymesh.send_mess(mac, msg1)
                gc.collect()
                time.sleep(1)
    print("Current available memory after chat exit: %d" % gc.mem_free())

def OnMWS2Logging(microWebSrv2, msg, msgType) :
    print('Log from custom function: %s' % msg)

# ============================================================================
# ============================================================================
# ============================================================================

print()

# send AT command to modem and return response as list
def at(cmd):
    print("modem command: {}".format(cmd))
    r = lte.send_at_cmd(cmd).split('\r\n')
    r = list(filter(None, r))
    print("response={}".format(r))
    return r

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
    print(node_config_list)
    for i in range(len(node_config_list)):
        temp_list = list(node_config_list[i].split(', '))
        node_config_dict[temp_list[0]] = temp_list[1]
    return node_config_dict

def create_house_dict():
    house_dict = {}
    with open('/sd/lib/houses.txt') as f:
        house_list = f.read().split('\r\n')
        f.close()
    for i in range(len(house_list)):
        temp_list = list(house_list[i].split(', '))
        house_dict[temp_list[0]] = int(temp_list[1])
    return house_dict

def add_node_to_text(msg):
    node_from_string = msg[12:]
    with open('/sd/lib/houses.txt', 'a') as f:
        f.write('\r\n')
        f.write(node_from_string)
        f.close()
    house_dict = create_house_dict()
    return house_dict

def send_nodes(sending_mac):
    house_dict = create_house_dict()
    msg = make_message_status(str(house_dict))
    time.sleep(1)
    with _chatLock :
        for ws in _chatWebSockets :
                ws.SendTextMessage(msg)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(2)

def sending_gps(sending_mac):
    if pytrack_s == True:
        coord = l76.coordinates()
        msg = make_message_status(str(coord))
        time.sleep(1)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(2)
    elif pytrack_s == False:
        no_gps = "This node doesn't have GPS"
        msg = make_message_status(no_gps)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(2)

def send_baro(sending_mac):
    if pysense_s == True:
        if len(sending_mac) == 0:
            print("Mac address format wrong")
            return
        msg1 = make_message_status(("MPL3115A2 temperature: " + str(mp.temperature())+
                " Altitude: " + str(mp.altitude())))
        pymesh.send_mess(sending_mac, str(msg1))
        time.sleep(2)
    elif pysense_s == False:
        no_baro = "This node doesn't have Baro"
        msg = make_message_status(no_baro)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(2)

def send_temp(sending_mac):
    if pysense_s == True:
        if len(sending_mac) == 0:
            print("Mac address format wrong")
            return
        msg1 = make_message_status(("Temperature: " + str(si.temperature())+
                " deg C and Relative Humidity: " + str(si.humidity()) + " %RH"))
        pymesh.send_mess(sending_mac, str(msg1))
        time.sleep(2)
    elif pysense_s == False:
        no_temp = "This node doesn't have Temp"
        msg = make_message_status(no_temp)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
            pymesh.send_mess(sending_mac, str(msg))
            time.sleep(2)

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
        time.sleep(3)

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
        time.sleep(2)

def first_time_set():
    current_time = utime.localtime()
    if current_time[0] == 1970:
        print("Time's wrong, send request to fix")
        wake = make_message_status("wake up 1!")
        time.sleep(1)
        pymesh.send_mess(1, str(wake))
        time.sleep(3)
        msg = ("JM set my time %s" % str(mac))
        pymesh.send_mess(1, str(msg))
        time.sleep(2)
    else:
        print("Time is correct")

def set_my_time(sending_mac):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
    else:
        now_time = utime.localtime()
        print(str(now_time))
        msg = ("JM set time 01 %s" % str(now_time))
        time.sleep(1)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(2)

def how_time_set(sending_mac):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
    else:
        now_time = current_time()
        msg = make_message_status(("Current:" + now_time + " Else, (year, month, day, hours, minutes, seconds, micros, timezone)"))
        time.sleep(1)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(2)

def get_macs_for_mess():
    house_mac_mess_list = []
    for k, v in house_dict.items():
        if v == 20 or v ==15 or v==16:
            print("Not adding repeaters to list")
        else:
            house_mac_mess_list.append(v)
    print("House mess list %s" % house_mac_mess_list)
    return house_mac_mess_list


def mac_to_house(mac):
    for k, v in house_dict.items():
        if mac == v:
            return k

def mac_to_house_list_string(macs):
    house_list = []
    for mac in macs:
        house = mac_to_house(mac)
        house_list.append(house)
    house_list_string = ' Houses online are: '
    for x in house_list:
        house_list_string += (x) + ' , '
    return house_list_string

def pop_mesh_pairs_list():
    mps = pymesh.mesh.get_mesh_pairs()
    have_mps = False
    while have_mps == False:
        time.sleep(1)
        mps = pymesh.mesh.get_mesh_pairs()
        time.sleep(2)
        print(mps)
        if len(mps) != 0:
            have_mps = True
    return mps

def find_leader():
    node_state = pymesh.status_str()
    print("Node state : %s" % str(node_state))
    my_mac = str(pymesh.mesh.mesh.MAC)
    if node_state[:6] == 'Role 4':
        leader_mac = my_mac
    else:
        mps = pop_mesh_pairs_list()
        leader_mac = mps[0][1]
    return leader_mac


# Not fully useable while "mml" command only gets nodes connected to leader
def pop_mac_list():
    have_mac_list = False
    macs = pymesh.mesh.get_mesh_mac_list()
    for i in range(20):
        time.sleep(4)
        macs = pymesh.mesh.get_mesh_mac_list()
        if len(macs[0]) != 0:
            have_mac_list = True
            break
    # while len(macs[0]) == 0:
    #     time.sleep(4)
    #     macs = pymesh.mesh.get_mesh_mac_list()
    if have_mac_list == False:
        msg = "This node is not connected to a mesh, power cycle and/or move node"
        print(msg)
        with _chatLock :
            for ws in _chatWebSockets :
                    ws.SendTextMessage(msg)
    else:
        print("making mac list")
        mac_list = []
        for mac in macs[0]:
            mac_list.append(mac)
        house_online_string = mac_to_house_list_string(mac_list)

    return house_online_string

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
            time.sleep(1.5)
    except:
        if exp31 == True:
            msg = make_message_status("No ADC")
            with _chatLock :
                for ws in _chatWebSockets :
                        ws.SendTextMessage(msg)
                pymesh.send_mess(sending_mac, str(msg))
                time.sleep(1.5)

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
        time.sleep(3)

def send_leader_hi(leader):
    my_mac = str(pymesh.mesh.mesh.MAC)
    print(my_mac)
    print(leader)
    if my_mac == leader:
        print("Either this node is the leader or not connected to mesh, not saying hi")
    else:
        msg = ("JM add me %s" % my_mac)
        with _chatLock :
            pymesh.send_mess(leader, str(msg))
            print("add me sent")
            time.sleep(2)


def add_me_leader(sending_mac):
    print("Adding to mesh leader mac list")
    msg = make_message_status("Node Added")
    with open('/sd/www/leader_mesh_list.txt', 'a') as f:
        f.write(sending_mac)
        f.write('\r\n')
        f.close()
    with _chatLock :
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(2)

def ask_for_mesh_macs(leader):
    print("in mesh macs")
    my_mac = str(pymesh.mesh.mesh.MAC)
    msg = ("JM send mml %s" % my_mac)
    if leader == my_mac:
        print("read from file")
    else:
        with _chatLock :
            pymesh.send_mess(leader, str(msg))
            time.sleep(1)
            print("done mesh macs")
    time.sleep(5)

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

    print(mac_string)
    # temp_mac_list = mac_string.split(", ")
    temp_string = mac_string.strip("'")
    temp_mac_list = temp_string.split("', '")
    print("this is the split list %s" % temp_mac_list)
    mac_list = []
    mac_list = [int(i) for i in temp_mac_list]
    print(mac_list)
    return mac_list

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
        elif msg[:11] == "JM add node":
            house_dict = add_node_to_text(msg)
        elif msg[:13] == "JM send nodes":
            sending_mac = msg[14:]
            send_nodes(sending_mac)
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
try:
    house_dict = create_house_dict()
except:
    print("There's no SD card, WebAP won't work")

# read config file, or set default values

node_dict = create_node_config_dict()
print(node_dict)

NODE_SSID = node_dict['WIFI_SSID']
NODE_PASS = node_dict['WIFI_PASS']
NODE_MAC = node_dict['NODE_MAC']
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

wlan= WLAN()
wlan.deinit()
wlan = WLAN(mode=WLAN.AP, ssid=NODE_SSID, auth=(WLAN.WPA2, NODE_PASS), channel=11, antenna=WLAN.INT_ANT)
wlan.ifconfig(id=1, config=('192.168.1.1', '255.255.255.0', '192.168.1.1', '8.8.8.8'))

# if has_LTE == True:
#     print("instantiate LTE object")
#     lte = LTE()
#     print("delay 4 secs")
#     time.sleep(4.0)
#
#     if lte.isattached():
#         try:
#             print("LTE was already attached, disconnecting...")
#             if lte.isconnected():
#                 print("disconnect")
#                 lte.disconnect()
#         except:
#             print("Exception during disconnect")
#
#         try:
#             if lte.isattached():
#                 print("detach")
#                 lte.dettach()
#         except:
#             print("Exception during dettach")
#
#         try:
#             print("resetting modem...")
#             lte.reset()
#         except:
#             print("Exception during reset")
#
#         print("delay 5 secs")
#         time.sleep(5.0)
#
#     # enable network registration and location information, unsolicited result code
#     at('AT+CEREG=2')
#
#     # print("full functionality level")
#     at('AT+CFUN=1')
#     time.sleep(1.0)
#
#     # using Hologram SIM
#     at('AT+CGDCONT=1,"IP","hologram"')
#
#     print("attempt to attach cell modem to base station...")
#     # lte.attach()  # do not use attach with custom init for Hologram SIM
#
#     at("ATI")
#     time.sleep(2.0)
#
#     i = 0
#     while lte.isattached() == False:
#         # get EPS Network Registration Status:
#         # +CEREG: <stat>[,[<tac>],[<ci>],[<AcT>]]
#         # <tac> values:
#         # 0 - not registered
#         # 1 - registered, home network
#         # 2 - not registered, but searching...
#         # 3 - registration denied
#         # 4 - unknown (out of E-UTRAN coverage)
#         # 5 - registered, roaming
#         r = at('AT+CEREG?')
#         try:
#             r0 = r[0]  # +CREG: 2,<tac>
#             r0x = r0.split(',')     # ['+CREG: 2',<tac>]
#             tac = int(r0x[1])       # 0..5
#             print("tac={}".format(tac))
#         except IndexError:
#             tac = 0
#             print("Index Error!!!")
#
#         # get signal strength
#         # +CSQ: <rssi>,<ber>
#         # <rssi>: 0..31, 99-unknown
#         r = at('AT+CSQ')
#
#         # extended error report
#         # r = at('AT+CEER')
#
#         # if lte.isattached():
#         #    print("Modem attached (isattached() function worked)!!!")
#         #    break
#
#         # if (tac==1) or (tac==5):
#         #    print("Modem attached!!!")
#         #    break
#
#         i = i + 5
#         print("not attached: {} secs".format(i))
#
#         if (tac != 0):
#             blink(BLUE, tac)
#         else:
#             blink(RED, 1)
#
#         time.sleep(5)
#     time.sleep(60)
#     print("set mode to text")
#     at('AT+CMGF=1')
#     print("set to check messages on sim")
#     at('AT+CPMS="SM", "SM", "SM"')
#     print("check message at 2")
#     try:
#         at('AT+CMGL="all"')
#     except:
#         print("no message")
#
#     # time.sleep(.5)
#     # at('AT+CMGS="15084103870"\rWorking\0x1a')
#     # print("sent!")
#
#     at('AT+CEREG?')
#     # print("Attempt to connect")
#     # try:
#     #     lte.connect()
#     #     i = 0
#     #     while not lte.isconnected():
#     #         i = i + 1
#     #         print("not connected: {}".format(i))
#     #         blink(GREEN, 1)
#     #         time.sleep(1.0)
#     #
#     #     print("connected!!!")
#     #     pycom.rgbled(BLUE)
#     #
#     # except:
#     #     print("yeah, that broke")
#
#     def wait_for_200_seconds():
#         for i in range(120):
#             print(i)
#             time.sleep(1)
#         lte.disconnect()
#         try:
#             at('AT+CMGL="all"')
#         except:
#             print("no message")
#         lte.dettach()
#         print("disconnect")
#         for i in range(10):
#             blink(YELLOW,1)
#             time.sleep(1.0)
#
#     _thread.start_new_thread(wait_for_200_seconds, ())
#
#
#
#
#     # end of test, Red LED
#     print("end of test")



print("AP setting up");
# first_time_set()
pycom.rgbled(0x000A00)

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
print(node_state[:6])
leader = find_leader()
print("Current available memory after wifi ap loads: %d" % gc.mem_free())

if mac != leader:
    send_leader_hi(leader)
    print("sending hi")

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
