from machine import SD
from MicroWebSrv2  import *
from network import WLAN
from pycoproc import Pycoproc
from time          import sleep
from _thread       import allocate_lock

import os
import pycom
import socket
import time
import uos



# try:
from pymesh_config import PymeshConfig
# except:
#     from _pymesh_config import PymeshConfig

# try:
from pymesh import Pymesh
# except:
#     from _pymesh import Pymesh

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
    webSocket.OnTextMessage = OnWSChatTextMsg
    webSocket.OnClosed      = OnWSChatClosed
    addr = webSocket.Request.UserAddress
    my_mac = pymesh.mesh.mesh.MAC
    macs = pop_mac_list()
    houses_string = mac_to_house_list_string(macs)
    house = mac_to_house(my_mac)
    msg1 = ('<%s HAS JOINED THE CHAT>' % house)
    msg2 = ("List of current %s" % houses_string)
    with _chatLock :
        for ws in _chatWebSockets :
            ws.SendTextMessage('<%s HAS JOINED THE CHAT>' % house)
            ws.SendTextMessage("List of current %s" % houses_string)
        _chatWebSockets.append(webSocket)
        house = mac_to_house(my_mac)
        webSocket.SendTextMessage('<WELCOME %s>' % house)
        webSocket.SendTextMessage("List of current %s" % houses_string)
        pymesh.send_mess('ff03::1', msg1)
        pymesh.send_mess('ff03::1', msg2)
        # for mac in macs[0]:
        #     if mac == my_mac:
        #         print("skip")
        #     else:
        #         pymesh.send_mess(mac, msg1)
        #         time.sleep(2)
        #         pymesh.send_mess(mac, msg2)
        time.sleep(1)

# ------------------------------------------------------------------------

def OnWSChatTextMsg(webSocket, msg) :
    addr = webSocket.Request.UserAddress
    macs = pop_mac_list()
    my_mac = pymesh.mesh.mesh.MAC
    house = mac_to_house(my_mac)
    new_msg = ('%s: %s' % (str(house), msg))
    with _chatLock :
        for ws in _chatWebSockets :
            #ws.SendTextMessage(': %s' % new_msg)
            ws.SendTextMessage(str(new_msg))
        pymesh.send_mess('ff03::1', new_msg)
        # for mac in macs[0]:
        #     if mac == my_mac:
        #         continue
        #     else:
        #         pymesh.send_mess(mac, str(new_msg))
        #         time.sleep(2)

# ------------------------------------------------------------------------

def OnWSChatClosed(webSocket) :
    addr = webSocket.Request.UserAddress
    macs = pop_mac_list()
    my_mac = pymesh.mesh.mesh.MAC
    house = mac_to_house(my_mac)
    msg1 = ('<%s HAS LEFT THE CHAT>' % house)
    with _chatLock :
        if webSocket in _chatWebSockets :
            _chatWebSockets.remove(webSocket)
            for ws in _chatWebSockets :
                ws.SendTextMessage(msg1)
        pymesh.send_mess('ff03::1', msg1)
        # for mac in macs[0]:
        #     if mac == my_mac:
        #         continue
        #     else:
        #         pymesh.send_mess(mac, msg1)
        #         time.sleep(2)

def OnMWS2Logging(microWebSrv2, msg, msgType) :
    print('Log from custom function: %s' % msg)

# ============================================================================
# ============================================================================
# ============================================================================

print()

def mac_to_house(mac):
    house_dict = {"Repeater2" : 1,
                  "Bobs_House" : 2,
                  "Ranges_House" : 3,
                  "Repeater1" : 4,
                  "Jamies_House" : 5}
    for k, v in house_dict.items():
        if mac == v:
            return k

def mac_to_house_list_string(macs):
    house_list = []
    for mac in macs[0]:
        house = mac_to_house(mac)
        house_list.append(house)
    house_list_string = ' Houses online are: '
    for x in house_list:
        house_list_string += (x) + ' , '
    return house_list_string

def pop_mac_list():
    macs = pymesh.mesh.get_mesh_mac_list()
    while len(macs[0]) == 0:
        time.sleep(4)
        macs = pymesh.mesh.get_mesh_mac_list()
    return macs

def copy(s, t):
    try:
        f = open(t, 'rb')
    except:
        f = open(t, 'wb')
    s = open(s, "rb")
    while True:
        b = s.read(4096)
        if not b:
           break
        f.write(b)
    f.close()
    s.close()

def new_message_cb(rcv_ip, rcv_port, rcv_data):
    ''' callback triggered when a new packet arrived '''
    print('Incoming %d bytes from %s (port %d):' %
            (len(rcv_data), rcv_ip, rcv_port))
    # print(py.read_battery_voltage())
    #macs = pop_mac_list()
    msg = rcv_data.decode("utf-8")
    # if py.read_battery_voltage() < 3.2:
    #     own_mac = str(pymesh.mesh.mesh.MAC)
    #     with _chatLock :
    #         for ws in _chatWebSockets :
    #             ws.SendTextMessage('Mac Address %s has a low battery' % (own_mac))
    with _chatLock :
        for ws in _chatWebSockets :
            ws.SendTextMessage('%s' % (msg))

    f = open('/sd/www/chat.txt', 'a+')
    f.write('%s\n' % msg)
    f.close()
    print('Wrote msg to SD, chat.txt')

    for _ in range(3):
        pycom.rgbled(0x888888)
        time.sleep(.2)
        pycom.rgbled(0)
        time.sleep(.1)
    return

pycom.heartbeat(False)
try:
    sd = SD()
    os.mount(sd, '/sd')
    print("SD card mounted")
    try:
        f = open('/sd/www/chat.txt', 'r')
        print("Already a chat log")
    except:
        os.mkdir('/sd/www')
        f = open('/sd/www/chat.txt', 'w+')
        f.write("Chat log:\n")
        print("chat Log created")
    f.close()

    try:
        f = open('/sd/www/wschat.html', 'r')
        print("Chat is on SD card")
        c = open('/flash/www/wschat.html', 'r')
        count_of_f = len(f.read())
        count_of_c = len(c.read())
        f.close()
        c.close()
        print("Check if wschat has changed")
        if count_of_c != count_of_f:
            os.remove('/sd/www/wschat.html')
            copy('/flash/www/wschat.html', '/sd/www/wschat.html')
            print("Copied new wshchat")

    except:
        copy('/flash/www/wschat.html', '/sd/www/wschat.html')
        print("WSChat now on SD card")

    try:
        f = open('/sd/www/index.html', 'r')
        c = open('/flash/www/index.html', 'r')
        count_of_f = len(f.read())
        count_of_c = len(c.read())
        c.close()
        f.close()
        print("Did the index change?")
        if count_of_c != count_of_f:
            os.remove('/sd/www/index.html')
            copy('/flash/www/index.html', '/sd/www/index.html')
            print("copied new index")
    except:
        copy('/flash/www/index.html', '/sd/www/index.html')
        print("Index now on SD card")

    try:
        f = open('/sd/www/style.css', 'r')
        print("Style is already on SD card")
        f.close()
    except:
        copy('/flash/www/style.css', '/sd/www/style.css')
        print("Style now on SD card")
except:
    print("SD card not loaded, chat not saved")




# read config file, or set default values
pymesh_config = PymeshConfig.read_config()


#initialize Pymesh
pymesh = Pymesh(pymesh_config, new_message_cb)
py = Pycoproc()
# print("Battery Voltage is:")
# print(py.read_battery_voltage())

mac = pymesh.mac()
# if mac > 10:
#     pymesh.end_device(True)
if mac == 5:
    pymesh.leader_priority(255)

while not pymesh.is_connected():
    print(pymesh.status_str())
    time.sleep(3)

wlan= WLAN()
wlan.deinit()
wlan = WLAN(mode=WLAN.AP, ssid="Rangeshouse", auth=(WLAN.WPA2, 'lhvwpass'), channel=11, antenna=WLAN.INT_ANT)
wlan.ifconfig(id=1, config=('192.168.1.1', '255.255.255.0', '192.168.1.1', '8.8.8.8'))

print("AP setting up");


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
