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
import ssl
import socket
import time
import utime
import uos

# try:
from pymesh_config import PymeshConfig
# except:
#     from _pymesh_config import PymeshConfig
try:
    from network import LTE
except:
    print("Not a FIPY")

# try:
from pymesh import Pymesh
# except:
#     from _pymesh import Pymesh

# house_dict = {"Jamies_House" : 1,
#               "Bobs_House" : 2,
#               "Ranges_House" : 3,
#               "Johns_House" : 4,
#               "Dennis_House" : 5,
#               "Marks_House" : 6,
#               "Susans_House" : 7,
#               "Tams_House" : 8,
#               "Bens_House" : 9,
#               "Garage" : 10,
#               "Repeater1" : 15,
#               "MountainRepeater" : 20,
#               "Portable1" : 25,
#               "Portable2" : 26,
#               "LTE1" : 50,
#               }

lh_mesh_version = "1.0.5"

# ============================================================================

@WebRoute(GET, '/test-redir')
def RequestTestRedirect(microWebSrv2, request) :
    request.Response.ReturnRedirect('/sd/chat.txt')

# ============================================================================

def OnWebSocketAccepted(microWebSrv2, webSocket) :
    print('Example WebSocket accepted:')
    print('   - User   : %s:%s' % webSocket.Request.UserAddress)
    print('   - Path   : %s'    % webSocket.Request.Path)
    print('   - Origin : %s'    % webSocket.Request.Origin)
    first_time_set()
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
    macs = get_macs_for_mess()
    houses_string = pop_mac_list()
    house = mac_to_house(my_mac)
    msg1 = make_message_status(('<%s HAS JOINED THE CHAT>' % house))
    # msg2 = ("List of current %s" % houses_string)
    msg_update = last_10_messages()
    with _chatLock :
        for ws in _chatWebSockets :
            ws.SendTextMessage('<%s HAS JOINED THE CHAT>' % house)
            gc.collect()
            # ws.SendTextMessage("List of current %s" % houses_string)
        _chatWebSockets.append(webSocket)
        house = mac_to_house(my_mac)
        webSocket.SendTextMessage('<WELCOME %s>' % house)
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
    macs = get_macs_for_mess()
    my_mac = pymesh.mesh.mesh.MAC
    house = mac_to_house(my_mac)
    new_msg = ('%s: %s' % (str(house), msg))
    now_time = current_time()
    with _chatLock :
        for ws in _chatWebSockets :
            #ws.SendTextMessage(': %s' % new_msg)
            ws.SendTextMessage(str(new_msg))
            gc.collect()
        # pymesh.send_mess('ff03::1', new_msg)
        for mac in macs:
            if mac == my_mac:
                continue
            else:
                pymesh.send_mess(mac, str(new_msg))
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
    macs = get_macs_for_mess()
    my_mac = pymesh.mesh.mesh.MAC
    house = mac_to_house(my_mac)
    msg1 = make_message_status(('<%s HAS LEFT THE CHAT>' % house))
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

def last_10_messages():
    with open('/sd/www/chat.txt', 'r') as f:
        all_messages = f.read().split('\n')
        f.close()
    last_messages = all_messages[-11:]
    return last_messages

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
wlan = WLAN(mode=WLAN.AP, ssid="DennisHouse", auth=(WLAN.WPA2, 'lhvwpass'), channel=11, antenna=WLAN.INT_ANT)
wlan.ifconfig(id=1, config=('192.168.1.1', '255.255.255.0', '192.168.1.1', '8.8.8.8'))

print("AP setting up");
first_time_set()
pycom.rgbled(0x000A00)

# # send AT command to modem and return response as list
# def at(cmd):
#     print("modem command: {}".format(cmd))
#     r = lte.send_at_cmd(cmd).split('\r\n')
#     r = list(filter(None, r))
#     print("response={}".format(r))
#     return r
#
# try:
#     print("instantiate LTE object")
#     lte = LTE(carrier="verizon")
#     print("delay 4 secs")
#     time.sleep(4.0)
#
#     print("reset modem")
#     try:
#         lte.reset()
#     except:
#         print("Exception during reset")
#
#     print("delay 5 secs")
#     time.sleep(5.0)
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
#         print("attached")
# except:
#     print("Not a fipy")

# try:
#     lte = LTE()    # instantiate the LTE object
#     lte.send_at_cmd('AT^RESET')
#     print("Resestted modem")
#     time.sleep(1)
#     lte.attach(apn='hologram')        # attach the cellular modem to a base station, initially it was lte.attach()
#     print( " While loop1") # print stmt to check on terminal
#     time.sleep(5) # added 5 seconds wait
#     pycom.rgbled(0x0000ff) # BLUE LED
#     while not lte.isattached():
#         print('Signal:%s'%lte.send_at_cmd('AT+CSQ'))
#         lte.send_at_cmd('AT+CSQ')
#         print('Status:%s '%lte.send_at_cmd('AT+CEER'))
#         lte.send_at_cmd('AT+CEER')
#         time.sleep(5)  # originally 0.25 changed to 5.0
#         lte.attach()
#     lte.connect(cid=3)       # start a data session and obtain an IP address
#     print( " While loop2")
#     pycom.rgbled(0x00ff00) # GREEN LED
#     while not lte.isconnected():
#         time.sleep(0.25)
#
#     s = socket.socket()
#     s = ssl.wrap_socket(s)
#     s.connect(socket.getaddrinfo('www.google.com', 443)[0][-1])
#     s.send(b"GET / HTTP/1.0\r\n\r\n")
#     print(s.recv(4096))
#     s.close()
#
#     lte.disconnect()
#     lte.dettach()
#     print( " While end loop")
#     pycom.rgbled(0xff0000) # RED LED, if it reached here we were successful
# except:
#     print("Node is not a FIPY")

# Loads the PyhtmlTemplate module globally and configure it,
pyhtmlMod = MicroWebSrv2.LoadModule('PyhtmlTemplate')
pyhtmlMod.ShowDebug = True
pyhtmlMod.SetGlobalVar('TestVar', 12345)

# Loads the WebSockets module globally and configure it,
wsMod = MicroWebSrv2.LoadModule('WebSockets')
wsMod.OnWebSocketAccepted = OnWebSocketAccepted

# Instanciates the MicroWebSrv2 class,
mws2 = MicroWebSrv2()
mws2.BindAddress = ('192.168.1.1', 80)
mws2.RootPath = '/sd/www'
# SSL is not correctly supported on MicroPython.
# But you can uncomment the following for standard Python.
# mws2.EnableSSL( certFile = 'SSL-Cert/openhc2.crt',
#                 keyFile  = 'SSL-Cert/openhc2.key' )

# For embedded MicroPython, use a very light configuration,
mws2.SetEmbeddedConfig()
mws2.OnLogging = OnMWS2Logging

# All pages not found will be redirected to the home '/',
mws2.NotFoundURL = '/'

# Starts the server as easily as possible in managed mode,
mws2.StartManaged()

print("Current available memory after wifi ap loads: %d" % gc.mem_free())

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
