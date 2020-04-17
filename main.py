import chat_msg_funcs as cmf
import file_ops
import gc
import lte_funcs as ltef
import pycom
import socket
import _thread
import time
import utime

from MicroWebSrv2  import *
from network       import WLAN
from time          import sleep
from _thread       import allocate_lock
from pymesh        import Pymesh
from pymesh_config import PymeshConfig

lh_mesh_version = "1.1.7"

# ============================================================================

@WebRoute(GET, '/test-redir')
def RequestTestRedirect(microWebSrv2, request) :
    request.Response.ReturnRedirect('/sd/index.html')

# ============================================================================

@WebRoute(GET, '/comms', name='Comms1/2')
def RequestTestPost(microWebSrv2, request) :
    # check for LTE messages if LTE Modem
    try:
        print("checking for LTE msgs")
        gc.collect()
        sms_temp = ltef.get_sms(lte_comms)
        lte_status_msg = "This node has LTE, last pulled messages listed below"
    except:
        print("Node doesn't have LTE, request list from LTE NODE.")
        lte_status_msg = "Node doesn't have LTE, request list from LTE NODE."
    time.sleep(5)

    with open('/sd/www/sms.txt', 'r') as f:
        sms_temp = f.read().split('\r\n')
        f.close()

    SMS = [string for string in sms_temp if string != ""]

    SMS = SMS[-5:]
    try:
        sms1 = SMS[0]
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
                %s<br />
                Refresh this page for latest SMS messages.<br />
                <br />
                Add html for sending messages to external chat rooms, SMS, <br />
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
                <br />
                %s<br />
                %s<br />
                %s<br />
                %s<br />
                %s<br />
    </html>
    """ % (lte_status_msg, node.node_name, sms1, sms2, sms3, sms4, sms5)
    request.Response.ReturnOk(content)

# ------------------------------------------------------------------------

@WebRoute(POST, '/comms', name='Comms2/2')
def RequestTestPost(microWebSrv2, request) :
    data = request.GetPostedURLEncodedForm()
    print("This space to send SMS and BR requests")
    if data['SMSNUM'] != 0 and data['SMSMSG'] != 0:
        try:
            ltef.lte_send_sms(lte_comms, data['SMSNUM'], data['SMSMSG'])
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
            How to display webpage scrape<br />
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
                A really fubar entry will lock up the node and require a hard reset<br />
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
    """ % (request.UserAddress[0], node.node_ssid, node.node_pass, node.mac, node.node_name, node.mesh_freq, node.mesh_band, node.mesh_spred, node.mesh_key, NODE_TIME)
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

        node.set_js_time(device_time)

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
        node.write_json_config_file(mac, mesh_freq, mesh_band, spread_fact, mesh_key)
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

@WebRoute(GET, '/node-diag', name='NodeDiag1/2')
def RequestTestPost(microWebSrv2, request) :
    NODE_STATE = pymesh.status_str()
    try:
        HTML_LEADER = node.find_leader()
        NODE_MML_LEN = len(RECEIVED_MAC_LIST)
        NODE_MML = RECEIVED_MAC_LIST
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
    """ % (NODE_STATE, node.mac, NODE_MML_LEN, NODE_MML, HTML_LEADER)
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
                Or go to the ack log and refresh to see if message was received: « <a href="/ack_log.txt">Ack Log</a> »
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
    leader = node.find_leader()
    node.send_leader_hi(leader)
    if node.mac == leader:
        macs = node.leader_gets_own_mesh_macs()
    else:
        node.ask_for_mesh_macs()
    if webSocket.Request.Path.lower() == '/wschat' :
        WSJoinChat(webSocket)
    else :
        webSocket.OnTextMessage   = OnWebSocketTextMsg
        webSocket.OnBinaryMessage = OnWebSocketBinaryMsg
        webSocket.OnClosed        = OnWebSocketClosed

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
    print("Ask leader for mac list")
    leader = node.find_leader()
    if node.mac == leader:
        macs = node.leader_gets_own_mesh_macs()
    else:
        try:
            macs = RECEIVED_MAC_LIST
        except:
            time.sleep(1)
            node.ask_for_mesh_macs()
            time.sleep(1)
            try:
                macs = RECEIVED_MAC_LIST
            except:
                print("somethings locked up")
                with _chatLock :
                    webSocket.SendTextMessage('No nodes have joined chat, wait and refresh page')

    print("The current macs are %s" % macs)
    msg1 = node.make_message_status(('A user from %s has joined>' % node.node_name))
    msg_update = node.last_10_messages()
    with _chatLock :
        for ws in _chatWebSockets :
            gc.collect()
        _chatWebSockets.append(webSocket)
        for i in range(len(msg_update)-1):
            webSocket.SendTextMessage('Previous MSG: %s' % msg_update[i])
            gc.collect()
        for mac in macs:
            if str(mac) == str(node.mac):
                print("skip")
            else:
                pymesh.send_mess(mac, msg1)
                gc.collect()
                time.sleep(1)
    print("Current available memory after chat join: %d" % gc.mem_free())

# ------------------------------------------------------------------------

def OnWSChatTextMsg(webSocket, msg) :
    gc.collect()
    leader = node.find_leader()
    node.send_leader_hi(leader)
    time.sleep(1)
    if node.mac == leader:
        print("Will get macs from file")
    else:
        node.ask_for_mesh_macs()
    time.sleep(1)
    addr = webSocket.Request.UserAddress
    if node.mac == leader:
        macs = node.leader_gets_own_mesh_macs()
    else:
        try:
            macs = RECEIVED_MAC_LIST
        except:
            time.sleep(1)
            node.ask_for_mesh_macs()
            time.sleep(1)
            try:
                macs = RECEIVED_MAC_LIST
            except:
                print("somethings locked up")
                with _chatLock :
                    webSocket.SendTextMessage('No nodes have joined chat, wait and refresh page')
    len_mac = (len(macs)-1)
    now_time = node.current_time()
    with _chatLock :
        for ws in _chatWebSockets :
            self_node_msg = ("Sent to %s nodes: %s" % (len_mac, msg))
            ws.SendTextMessage(str(self_node_msg))
            gc.collect()
        for mac in macs:
            if str(mac) == str(node.mac):
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
    try:
        macs = RECEIVED_MAC_LIST
    except:
        time.sleep(1)
        node.ask_for_mesh_macs()
        time.sleep(1)
        try:
            macs = RECEIVED_MAC_LIST
        except:
            print("somethings locked up")
    msg1 = node.make_message_status(('<User HAS LEFT THE CHAT>'))
    pycom.rgbled(0x000A00)
    with _chatLock :
        if webSocket in _chatWebSockets :
            _chatWebSockets.remove(webSocket)
            for ws in _chatWebSockets :
                ws.SendTextMessage(msg1)
                gc.collect()
    print("Current available memory after chat exit: %d" % gc.mem_free())

def OnMWS2Logging(microWebSrv2, msg, msgType) :
    print('Log from custom function: %s' % msg)

# ============================================================================

print("====================================================================")

def new_message_cb(rcv_ip, rcv_port, rcv_data):
    ''' callback triggered when a new packet arrived '''
    print('Incoming %d bytes from %s (port %d):' %
            (len(rcv_data), rcv_ip, rcv_port))
    now_time = node.current_time()
    msg = rcv_data.decode("utf-8")
    if msg[:6] == "STATUS":
        f = open('/sd/www/status_log.txt', 'a+')
        f.write('%s %s\n' % (now_time, msg))
        f.close()
        print('Wrote status msg to log')

    elif msg[:2] == "JM":
        if msg[:13] == "JM batt level":
            sending_mac = msg[14:]
            node.send_battery_voltage(sending_mac)
        elif msg[:12] == "JM send self":
            sending_mac = msg[13:]
            node.send_self_info(sending_mac)
        elif msg[:8] == "JM RESET":
            node.node_reset()
        elif msg[:11] == "JM set time":
            sending_mac = msg[12:14]
            node.set_time(sending_mac, msg)
        elif msg[:10] == "JM how set":
            sending_mac = msg[11:]
            node.how_time_set(sending_mac)
        elif msg[:11] == "JM send GPS":
            sending_mac = msg[12:]
            node.sending_gps(sending_mac)
        elif msg[:12] == "JM send baro":
            sending_mac = msg[13:]
            node.send_baro(sending_mac)
        elif msg[:12] == "JM send temp":
            sending_mac = msg[13:]
            node.send_temp(sending_mac)
        elif msg[:14] == "JM set my time":
            sending_mac = msg[15:]
            node.set_my_time(sending_mac)
        elif msg[:16] == "JM set your time":
            node.first_time_set()
        elif msg[:11] == "JM send swv":
            sending_mac = msg[12:]
            node.send_mesh_version(sending_mac, lh_mesh_version)
        elif msg[:9] == "JM add me":
            sending_mac = msg[10:]
            node.add_me_leader(sending_mac)
        elif msg[:11] == "JM send mml":
            sending_mac = msg[12:]
            node.send_back_mml(sending_mac)
        elif msg[:14] == "JM receive mml":
            msg = msg[15:]
            global RECEIVED_MAC_LIST
            RECEIVED_MAC_LIST = node.save_mml(msg)
        elif msg[:12] == "JM send name":
            sending_mac = msg[13:]
            node.send_name(sending_mac)
        elif msg[:11] == "JM send sms":
            sen_to_number = msg[12:23]
            print(sen_to_number)
            sms_msg = msg[24:]
            print(sms_msg)
            try:
                print("Sending SMS")
                ltef.lte_send_sms(lte_comms, sen_to_number, sms_msg)
            except:
                print("No LTE")
        elif msg[:11] == "JM send csq":
            sending_mac = msg[12:]
            ltef.get_signal_strength(lte_comms)
        elif msg[:11] == "JM read sms":
            sending_mac = msg[12:]
            ltef.lte_check_read_sms(lte_comms)
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
        gc.collect()
    return

gc.enable()
print("Current available memory: %d" % gc.mem_free())
pycom.heartbeat(False)

# Build SD files system
file_ops.sd_setup()
#Load pymesh settings, ead from SD card
pymesh_config = PymeshConfig.read_config()
print("====================================================================")

#initialize Pymesh
pymesh = Pymesh(pymesh_config, new_message_cb)
node = cmf.NodeFuncs(pymesh)

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
wlan = WLAN(mode=WLAN.AP, ssid=node.node_ssid, auth=(WLAN.WPA2, node.node_pass), channel=11, antenna=WLAN.INT_ANT)
wlan.ifconfig(id=1, config=('192.168.1.1', '255.255.255.0', '192.168.1.1', '8.8.8.8'))

print("====================================================================")


print("AP setting up");

node.first_time_set()

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

# Check if LTE exists and start if it does
lte_comms = ltef.start_lte()
gc.collect()
node.wake_up_leader_to_add()

print("====================================================================")


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
gc.collect()
print()
# ============================================================================
