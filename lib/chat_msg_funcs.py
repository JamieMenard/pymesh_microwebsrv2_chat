from L76GNSS import L76GNSS
from machine import RTC
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE

from pymesh import Pymesh
from pycoproc import Pycoproc

import gc
import machine
import os
import time
import _thread
import utime
import uos

class NodeFuncs:
    def __init__(self, pymesh):
        self.pymesh = pymesh
        # read config file, or set default values
        node_dict = self.create_node_config_dict()
        self.node_ssid = node_dict['WIFI_SSID']
        self.node_pass = node_dict['WIFI_PASS']
        self.node_name = node_dict['NODE_NAME']
        self.mesh_freq = node_dict['MESH_FREQ']
        self.mesh_band = node_dict['MESH_BAND']
        self.mesh_spred = node_dict['SPREAD_FACT']
        self.mesh_key = node_dict['MESH_KEY']

        if uos.uname().sysname == 'FiPy':
            self.has_lte = True
        else:
            self.has_lte = False
        self.mac = str(pymesh.mesh.mesh.MAC)
        try:
            self.py = Pycoproc()
        except:
            self.exp31 = True
        self.rtc = RTC()
        try:
            self.l76 = L76GNSS(py, timeout=30)
            self.pytrack_s = True
            print("Pytrack")
        except:
            self.pytrack_s = False

        try:
            self.si = SI7006A20(py)
            self.mp = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters. Mode may also be set to PRESSURE, returning a value in Pascals
            self.mpp = MPL3115A2(py,mode=PRESSURE) # Returns pressure in Pa. Mode may also be set to ALTITUDE, returning a value in meters
            self.pysense_s = True
            print("Pysense")
        except:
            self.pysense_s = False

        if self.pysense_s == False and self.pytrack_s == False:
            print("EXP 3.1")

# ============================================================================
# Utility functions

    def make_message_status(self, msg):
        status_msg = ("STATUS: %s" % msg)
        return status_msg

    def write_json_config_file(self, mac, freq, band, sprd, key):
        json_config = ('{"ble_api": false, "autostart": true, "ble_name_prefix": "PyGo ", "debug": 5, "LoRa": {"sf": %s, "region": 8, "freq": %s, "bandwidth": %s, "tx_power": 14}, "MAC": %s, "Pymesh": {"key": "%s"}}' % (sprd, freq, band, mac, key))
        try:
            with open('/sd/www/pymesh_config.json', 'w+') as f:
                f.write(str(json_config))
                f.close()
        except:
            print("File didn't write")

    def last_10_messages(self):
        with open('/sd/www/chat.txt', 'r') as f:
            all_messages = f.read().split('\n')
            f.close()
        last_messages = all_messages[-11:]
        return last_messages

    def create_node_config_dict(self):
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

    def node_reset(self):
        machine.reset()

# ============================================================================
# Functions to find mesh status

    def save_mml(self, msg):
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

    def leader_gets_own_mesh_macs(self):
        with open('/sd/www/leader_mesh_list.txt') as f:
            temp_mac_list = f.read().split('\r\n')
            f.close()
        mac_list = list( dict.fromkeys(temp_mac_list[:-1]) )
        mac_list.append(self.mac)
        #compare this list to mml list
        mml_macs = self.pymesh.mesh.get_mesh_mac_list()
        for i in range(20):
            time.sleep(4)
            mml_macs = self.pymesh.mesh.get_mesh_mac_list()
            if len(mml_macs.get(0)) != 0:
                have_mac_list = True
                break
            else:
                mml_macs = []
        string_mml_macs = [str(i) for i in mml_macs.get(0)]
        resulting_list = list(mac_list)
        resulting_list.extend(x for x in string_mml_macs if x not in resulting_list)
        mac_list = resulting_list
        return mac_list

    def pop_mesh_pairs_list(self):
        mps = self.pymesh.mesh.get_mesh_pairs()
        if len(mps) == 0:
            time.sleep(5)
            mps = self.pymesh.mesh.get_mesh_pairs()
            if len(mps) == 0:
                time.sleep(5)
                mps = self.pymesh.mesh.get_mesh_pairs()
            else:
                return mps
        else:
            return mps

# ============================================================================
# Time related functions

    def set_js_time(self, jtime):
        time_from_jtime = jtime[2:-2]
        jtime_from_message_tuple = tuple(map(int, time_from_jtime.split(", ")))
        self.rtc.init(jtime_from_message_tuple)
        print("Time set")

    def set_my_time(self, sending_mac):
        if len(sending_mac) == 0:
            print("Mac address format wrong")
        else:
            now_time = utime.localtime()
            msg = ("JM set time 01 %s" % str(now_time))
            time.sleep(1)
            self.pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

    def how_time_set(self, sending_mac):
        if len(sending_mac) == 0:
            print("Mac address format wrong")
        else:
            now_time = self.current_time()
            msg = self.make_message_status(("Current:" + now_time + " Else, (year, month, day, hours, minutes, seconds, micros, timezone)"))
            time.sleep(1)
            self.pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

    def set_time(self, sending_mac, msg):
        if len(sending_mac) == 0:
            print("Mac address format wrong")
            return
        time_from_message_string = msg[16:-1]
        print(time_from_message_string)
        time_from_message_tuple = tuple(map(int, time_from_message_string.split(", ")))
        self.rtc.init(time_from_message_tuple)
        msg = self.make_message_status("Time Set")
        time.sleep(1)
        self.pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

    def format_time(self, given_time):
        format_time = ("[%d:%d %d/%d]"  % (given_time[3], given_time[4], given_time[1], given_time[2]))
        return format_time

    def current_time(self):
        current_time = utime.localtime()
        formatted_time = self.format_time(current_time)
        return formatted_time

    def first_time_set(self):
        current_time = utime.localtime()
        if current_time[0] == 1970:
            print("Time's wrong, send request to fix")
            wake = self.make_message_status("wake up 1!")
            time.sleep(1)
            self.pymesh.send_mess(1, str(wake))
            time.sleep(1)
            msg = ("JM set my time %s" % str(self.mac))
            self.pymesh.send_mess(1, str(msg))
            time.sleep(1)
        else:
            print("Time is correct")

# ============================================================================
# Sending node info functions

    def send_mesh_version(self, sending_mac, lh_mesh_version):
        if len(sending_mac) == 0:
            print("Mac address format wrong")
            return
        msg = self.make_message_status(("Node SW version: %s" % lh_mesh_version))
        time.sleep(1)
        self.pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

    def send_name(self, sending_mac):
        self.pymesh.send_mess(sending_mac, str(self.node_name))
        time.sleep(1)

    def send_self_info(self, sending_mac):
        if len(sending_mac) == 0:
            print("Mac address format wrong")
            return
        node_info = str(self.pymesh.mesh.get_node_info())
        msg = self.make_message_status(("self info: %s" % node_info))
        time.sleep(1)
        self.pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

# ============================================================================
# Leader related functions

    def find_leader(self):
        node_state = self.pymesh.status_str()
        print("Node state : %s" % str(node_state))
        mesh_mac_list = self.pymesh.mesh.get_mesh_mac_list()
        if node_state[:6] == 'Role 4':
            leader_mac = self.mac
        elif len(mesh_mac_list) == 2:
            leader_mac = mesh_mac_list.remove(self.mac)
        else:
            mps = self.pop_mesh_pairs_list()
            try:
                leader_mac = mps[0][1]
            except:
                leader_mac = self.mac
        return leader_mac

    def send_leader_hi(self, leader):
        if self.mac == leader:
            print("Either this node is the leader or not connected to mesh, not saying hi")
        else:
            msg = ("JM add me %s" % self.mac)
            self.pymesh.send_mess(leader, str(msg))
            time.sleep(1)

    def wake_up_leader_to_add(self):
        leader = self.find_leader()
        if self.mac != leader:
            self.send_leader_hi(leader)
            time.sleep(4)
            self.send_leader_hi(leader)

    def add_me_leader(self, sending_mac):
        print("Adding to mesh leader mac list")
        msg = self.make_message_status("Node Added")
        with open('/sd/www/leader_mesh_list.txt') as f:
            temp_mac_list = f.read().split('\r\n')
            f.close()
        if (sending_mac in temp_mac_list):
            print("Node already in list")
            self.pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)
        else:
            with open('/sd/www/leader_mesh_list.txt', 'a') as f:
                f.write(sending_mac)
                f.write('\r\n')
                f.close()
            self.pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

    def ask_for_mesh_macs(self):
        leader = self.find_leader()
        msg = ("JM send mml %s" % self.mac)
        self.pymesh.send_mess(leader, str(msg))
        time.sleep(1)
        time.sleep(1)

    def send_back_mml(self, sending_mac):
        temp_mac_list = []
        with open('/sd/www/leader_mesh_list.txt') as f:
            temp_mac_list = f.read().split('\r\n')
            f.close()
        mac_list = list( dict.fromkeys(temp_mac_list[:-1]) )
        mac_list.append(self.mac) 
        #compare this list to mml list
        mml_macs = self.pymesh.mesh.get_mesh_mac_list()
        for i in range(20):
            time.sleep(4)
            mml_macs = self.pymesh.mesh.get_mesh_mac_list()
            if len(mml_macs.get(0)) != 0:
                have_mac_list = True
                break
            else:
                mml_macs = []
        string_mml_macs = [str(i) for i in mml_macs.get(0)]
        resulting_list = list(mac_list)
        resulting_list.extend(x for x in string_mml_macs if x not in resulting_list)
        mac_list = resulting_list
        msg = ("JM receive mml %s" % str(mac_list))
        self.pymesh.send_mess(sending_mac, str(msg))
        time.sleep(1)

# ============================================================================
# Sensor data messages

    def send_battery_voltage(self, sending_mac):
        if len(sending_mac) == 0:
            print("Mac address format wrong")
            return
        try:
            volts = str(self.py.read_battery_voltage())
            msg = self.make_message_status(('Mac Address %s battery level is: %s' % (self.mac, volts)))
            time.sleep(1)
            self.pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)
        except:
            if self.exp31 == True:
                msg = self.make_message_status("No ADC")
                self.pymesh.send_mess(sending_mac, str(msg))
                time.sleep(1)

    def send_temp(self, sending_mac):
        if self.pysense_s == True:
            if len(sending_mac) == 0:
                print("Mac address format wrong")
                return
            msg1 = self.make_message_status(("Temperature: " + str(self.si.temperature())+
                    " deg C and Relative Humidity: " + str(self.si.humidity()) + " %RH"))
            self.pymesh.send_mess(sending_mac, str(msg1))
            time.sleep(1)
        elif self.pysense_s == False:
            no_temp = "This node doesn't have Temp"
            msg = self.make_message_status(no_temp)
            self.pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

    def send_baro(self, sending_mac):
        if self.pysense_s == True:
            if len(sending_mac) == 0:
                print("Mac address format wrong")
                return
            msg1 = self.make_message_status(("MPL3115A2 temperature: " + str(self.mp.temperature())+
                    " Altitude: " + str(self.mp.altitude())))
            self.pymesh.send_mess(sending_mac, str(msg1))
            time.sleep(1)
        elif self.pysense_s == False:
            no_baro = "This node doesn't have Baro"
            msg = self.make_message_status(no_baro)
            self.pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

    def sending_gps(self, sending_mac):
        if self.pytrack_s == True:
            coord = self.l76.coordinates()
            msg = self.make_message_status(str(coord))
            time.sleep(1)
            self.pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)
        elif self.pytrack_s == False:
            no_gps = "This node doesn't have GPS"
            msg = self.make_message_status(no_gps)
            self.pymesh.send_mess(sending_mac, str(msg))
            time.sleep(1)

# ============================================================================
# Border node functions

    def ask_nodes_if_lte(mml):
        print("will have this ask nodes if LTE")

    def reply_if_lte(sending_mac):
        print("This will respond if LTE")

    def ask_nodes_if_BR(mml):
        print("This will ask if nodes are BR")

    def reply_if_BR(sending_mac):
        print("This will reply if node is BR")