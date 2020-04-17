import gc
import pycom
import socket
import ssl
import sys
import time
import _thread
import uos

try:
    from network import LTE
except:
    print("No LTE Modem")

def start_lte():
    if uos.uname().sysname == 'FiPy':
        try:
            lte_comms = LteComms()
            print("LTE communication being setup")
            time.sleep(5)
        except:
            print('still broken')

        try:
            print("Attaching LTE to network")
            gc.collect()
            _thread.start_new_thread(lte_comms.attach_LTE, ())
            gc.collect()
            return lte_comms
        except:
            print("Not attached")
    else:
        print("Not a fipy")


def get_sms(lte_comms):
    if uos.uname().sysname == 'FiPy':
        print("Starting to monitor for new SMS in 60 seconds")
        _thread.start_new_thread(lte_comms.receive_and_forward_to_chat, ())
        gc.collect()
    else:
        print("Not a fipy, not checking messages.")

def lte_send_sms(lte_comms, number, msg):
    lte_comms.send_sms(number, msg)

def get_signal_strength(lte_comms):
    lte_comms.signal_strength()

def lte_check_read_sms(lte_comms):
    lte_comms.check_read_sms()


class LteComms:
    def __init__(self):
        self.message_storage = 'AT+CPMS="SM", "SM", "SM"'
        gc.collect()
        try:
            self.lte = LTE()
            time.sleep(4)
        except:
            print("initialize LTE object?")
        self.lte.reset()
        time.sleep(4)
        print("delay 4 secs")


    def at(self, cmd):
        print("modem command: {}".format(cmd))
        r = self.lte.send_at_cmd(cmd).split('\r\n')
        r = list(filter(None, r))
        print("response={}".format(r))
        return r

    def attach_LTE(self):
        gc.collect()
        time.sleep(10.0)

        if self.lte.isattached():
            try:
                print("LTE was already attached, disconnecting...")
                if self.lte.isconnected():
                    print("disconnect")
                    self.lte.disconnect()
            except:
                print("Exception during disconnect")

            try:
                if self.lte.isattached():
                    print("detach")
                    self.lte.dettach()
            except:
                print("Exception during dettach")

            try:
                print("resetting modem...")
                self.lte.reset()
            except:
                print("Exception during reset")

            print("delay 5 secs")
            time.sleep(5.0)

        # enable network registration and location information, unsolicited result code
        self.at('AT+CEREG=2')

        # print("full functionality level")
        self.at('AT+CFUN=1')
        time.sleep(1.0)

        # using Hologram SIM
        self.at('AT+CGDCONT=1,"IP","hologram"')

        print("attempt to attach cell modem to base station...")
        # lte.attach()  # do not use attach with custom init for Hologram SIM

        self.at("ATI")
        time.sleep(2.0)

        i = 0
        while self.lte.isattached() == False:
            # get EPS Network Registration Status:
            # +CEREG: <stat>[,[<tac>],[<ci>],[<AcT>]]
            # <tac> values:
            # 0 - not registered
            # 1 - registered, home network
            # 2 - not registered, but searching...
            # 3 - registration denied
            # 4 - unknown (out of E-UTRAN coverage)
            # 5 - registered, roaming
            r = self.at('AT+CEREG?')
            try:
                r0 = r[0]  # +CREG: 2,<tac>
                r0x = r0.split(',')     # ['+CREG: 2',<tac>]
                tac = int(r0x[1])       # 0..5
                print("tac={}".format(tac))
            except IndexError:
                tac = 0
                print("Index Error!!!")

            # get signal strength
            # +CSQ: <rssi>,<ber>
            # <rssi>: 0..31, 99-unknown
            r = self.at('AT+CSQ')

            # extended error report
            # r =self.at('AT+CEER')

            # if lte.isattached():
            #    print("Modem attached (isattached() function worked)!!!")
            #    break

            # if (tac==1) or (tac==5):
            #    print("Modem attached!!!")
            #    break

            i = i + 5
            print("not attached: {} secs".format(i))

        # while self.lte.isattached():
        #     # self.receive_and_forward_to_chat()
        #     continue
        # print("Modem not attached")
        print("set to check messages on sim")
        self.at(self.message_storage)


    def connect_lte_data(self):
        self.at('AT+CEREG?')
        print("Attempt to connect")
        if self.lte.isattached() == False:
            print("Not attached, try again, will fail")
        else:
            print("Attached and continue")

        self.lte.connect()
        i = 0
        while not self.lte.isconnected():
            i = i + 1
            print("not connected: {}".format(i))
            time.sleep(1.0)

        print("LTE connected for data!!!") # also send this to chat
        # so just pymesh this to all nodes in leader_mesh_list
        while self.lte.isconnected():
            continue

    def scrape_webpage(self, url):
        s = socket.socket()
        s = ssl.wrap_socket(s)
        s.connect(socket.getaddrinfo(url, 443)[0][-1])
        s.send(b"GET / HTTP/1.0\r\n\r\n")
        print(s.recv(4096))
        s.close()

    def send_sms(self, number, msg):
        # this will somehow have to be connected to the chat with a JM msg1
        print("set mode to text")
        self.at('AT+CMGF=1')
        time.sleep(.5)
        # msg = ('AT+CMGS="%s"\r%s\0x1a' % (number, msg))
        # print(('ATTB+SQNSMSSEND="%s", "%s"' % (number, msg)))
        print('sendin an sms', end=' '); ans=self.lte.send_at_cmd(('AT+SQNSMSSEND="%s", "%s"' % (number, msg))).split('\r\n'); print(ans)
        # self.at(msg)
        time.sleep(4)
        print("sent!")

    def receive_and_forward_to_chat(self):
        # this will somehow have to be connected to the chat with a JM msg1
        print("set mode to text")
        self.at('AT+CMGF=1')
        msg_list = []
        msg_list = self.at('AT+CMGL="ALL"')
        number_of_messages = 0
        if len(msg_list) > 1:
            print("This'll print if there a msg")
            if len(msg_list) > 20:
                print("More then 10 messages, loop")
                i = 1
                while len(msg_list) > 20:
                    print("This is the inner loop running %s times" % i)
                    msg_list = self.at('AT+CMGL="ALL"')
                    number_of_messages += len(msg_list)
                    self.write_msg_to_file_and_delete(msg_list)
                    time.sleep(15)
                    i += 1
                print("This is to get the last group of messages")
                # you don't scan for messages while it sleep, almost Need
                # to run this in a thread in the background.
                time.sleep(10)
                msg_list = self.at('AT+CMGL="ALL"')
                number_of_messages += len(msg_list)
                self.write_msg_to_file_and_delete(msg_list)
            else:
                print("The list is less than 10, so straight to file")
                number_of_messages += len(msg_list)
                self.write_msg_to_file_and_delete(msg_list)
        else:
            print("This prints when no messages")
            self.at('AT+CMGD=1,4')
        # Cuz apparently you need to clean out the sim card, it only holds 10 msgs
        # at('AT+CMGD=1,4')
        time.sleep(5)
        actual_messages = (number_of_messages/2) - 1
        print(actual_messages)

    def msg_parse(self, msg_list):
        parsed_msg_list = []
        msg_list_string = "".join(msg_list)
        split_msg_list = msg_list_string.split('+CMGL:')
        for i in range(len(split_msg_list)):
            temp_string = str(split_msg_list[i])
            if temp_string[-2:] == 'OK':
                parsed_msg_list.append(temp_string[:-2])
            else:
                parsed_msg_list.append(temp_string)
        return parsed_msg_list

    def disconnect_LTE(self):
        self.lte.disconnect()
        print("LTE Data disconnected")
        # send to chat

    def unattach_lte(self):
        self.lte.detach(reset=True)
        print("LTE modem deattached")

    def signal_strength(self):
        self.at('AT+CSQ')

    def check_read_sms(self):
        self.at('AT+CMGF=1')
        msg_list =self.at('AT+CMGL="ALL"')
        print(msg_list)

    def write_msg_to_file_and_delete(self, msg_list):
        parsed_msg_list = self.msg_parse(msg_list)
        print("Writing to SMS log")
        f = open('/sd/www/sms.txt', 'a+')
        for i in range(len(parsed_msg_list)):
            if parsed_msg_list[i] != '\r\n':
                f.write(str(parsed_msg_list[i]))
                f.write('\r\n')
        f.close()
        self.at('AT+CMGD=1,4')

