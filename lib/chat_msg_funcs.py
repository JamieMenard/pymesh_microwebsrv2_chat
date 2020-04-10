from pymesh import Pymesh
from machine import RTC
import os
import time
import utime

def save_mml(msg):
    mac_string = msg[1:-1]
    temp_string = mac_string.strip("'")
    temp_mac_list = temp_string.split("', '")
    mac_list = []
    mac_list = [int(i) for i in temp_mac_list]
    mac_list = list( dict.fromkeys(mac_list) )
    with open('/sd/www/leader_mesh_list.txt', 'a') as f:
        for i in mac_list:
            f.write(str(i))
            f.write('\r\n')
        f.close()
    with open('/sd/www/leader_mesh_list.txt') as f:
        temp_mac_list = f.read().split('\r\n')
        f.close()
    temp_mac_list = list( dict.fromkeys(temp_mac_list[:-1]) )
    temp_without_empty_strings = [string for string in temp_mac_list if string != ""]
    os.remove('/sd/www/leader_mesh_list.txt')
    with open('/sd/www/leader_mesh_list.txt', 'w+') as f:
        for i in temp_without_empty_strings:
            f.write(str(i))
            f.write('\r\n')
        f.close()
    print("The current mac list is: %s" % mac_list)
    return mac_list

    def leader_gets_own_mesh_macs(pymesh):
        my_mac = str(pymesh.mesh.mesh.MAC)
        with open('/sd/www/leader_mesh_list.txt') as f:
            temp_mac_list = f.read().split('\r\n')
            f.close()
        mac_list = list( dict.fromkeys(temp_mac_list[:-1]) )
        mac_list.append(my_mac)
        return mac_list

def set_js_time(rtc, jtime):
    time_from_jtime = jtime[2:-2]
    jtime_from_message_tuple = tuple(map(int, time_from_jtime.split(", ")))
    rtc.init(jtime_from_message_tuple)
    print("Time set")

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

def first_time_set(pymesh):
    current_time = utime.localtime()
    my_mac = str(pymesh.mesh.mesh.MAC)
    if current_time[0] == 1970:
        print("Time's wrong, send request to fix")
        wake = make_message_status("wake up 1!")
        time.sleep(1)
        pymesh.send_mess(1, str(wake))
        time.sleep(1)
        msg = ("JM set my time %s" % str(my_mac))
        pymesh.send_mess(1, str(msg))
        time.sleep(1)
    else:
        print("Time is correct")

def set_my_time(pymesh, sending_mac):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
    else:
        now_time = utime.localtime()
        msg = ("JM set time 01 %s" % str(now_time))
        time.sleep(1)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

def pop_mesh_pairs_list(pymesh):
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

def how_time_set(pymesh, sending_mac):
    if len(sending_mac) == 0:
        print("Mac address format wrong")
    else:
        now_time = current_time()
        msg = make_message_status(("Current:" + now_time + " Else, (year, month, day, hours, minutes, seconds, micros, timezone)"))
        time.sleep(1)
        pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

def find_leader(pymesh):
    node_state = pymesh.status_str()
    print("Node state : %s" % str(node_state))
    my_mac = str(pymesh.mesh.mesh.MAC)
    mesh_mac_list = pymesh.mesh.get_mesh_mac_list()
    if node_state[:6] == 'Role 4':
        leader_mac = my_mac
    elif len(mesh_mac_list) == 2:
        leader_mac = mesh_mac_list.remove(my_mac)
    else:
        mps = pop_mesh_pairs_list(pymesh)
        try:
            leader_mac = mps[0][1]
        except:
            leader_mac = NODE_MAC
    return leader_mac

def write_json_config_file(mac, freq, band, sprd, key):
    json_config = ('{"ble_api": false, "autostart": true, "ble_name_prefix": "PyGo ", "debug": 5, "LoRa": {"sf": %s, "region": 8, "freq": %s, "bandwidth": %s, "tx_power": 14}, "MAC": %s, "Pymesh": {"key": "%s"}}' % (sprd, freq, band, mac, key))
    try:
        with open('/sd/www/pymesh_config.json', 'w+') as f:
            f.write(str(json_config))
            f.close()
    except:
        print("File didn't write")

def last_10_messages():
    with open('/sd/www/chat.txt', 'r') as f:
        all_messages = f.read().split('\n')
        f.close()
    last_messages = all_messages[-11:]
    return last_messages

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