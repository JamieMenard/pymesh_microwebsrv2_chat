import os
from machine import SD

def sd_setup():
    try:
        sd = SD()
        os.mount(sd, '/sd')
        print("SD card mounted")
        # try:
        #     os.remove('/sd/www/leader_mesh_list.txt')
        # except:
        #     print('did not delete')
        try:
            f = open('/sd/www/ack_log.txt', 'r')
            print("Already a ACK log, trimmed to last 100 ACKs")
            acks = f.readlines()
            f.close()
            os.remove('/sd/www/ack_log.txt')
            n = open('/sd/www/ack_log.txt', 'w+')
            for i in acks[-50:]:
                n.write(i)
            n.close()
        except:
            try:
                os.mkdir('/sd/www')
                f = open('/sd/www/ack_log.txt', 'w+')
                f.write("ACK log:\n")
            except:
                f = open('/sd/www/ack_log.txt', 'w+')
                f.write("ACK log:\n")
            print("ACK Log created")
        f.close()

        try:
            f = open('/sd/www/status_log.txt', 'r')
            print("Already a status log, trimmed to last 100 entries.")
            status = f.readlines()
            f.close()
            os.remove('/sd/www/status_log.txt')
            n = open('/sd/www/status_log.txt', 'w+')
            for i in status[-50:]:
                n.write(i)
            n.close()
        except:
            try:
                os.mkdir('/sd/www')
                f = open('/sd/www/status_log.txt', 'w+')
                f.write("Status log:\n")
            except:
                f = open('/sd/www/status_log.txt', 'w+')
                f.write("Status log:\n")
            print("Status Log created")
        f.close()

        try:
            f = open('/sd/www/chat.txt', 'r')
            print("Already a chat log, trimmed to last 100 entries.")
            chats = f.readlines()
            f.close()
            os.remove('/sd/www/chat.txt')
            n = open('/sd/www/chat.txt', 'w+')
            for i in chats[-50:]:
                n.write(i)
            n.close()
        except:
            try:
                os.mkdir('/sd/www')
                f = open('/sd/www/chat.txt', 'w+')
                f.write("Chat log:\n")
            except:
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

        try:
            print("Check Node Config status")
            f = open('/sd/www/node_config.txt', 'r')
            f.close()
            print("Node Config is on SD Card")

        except:
            try:
                os.mkdir('/sd/www')
                copy('/flash/node_config.txt', '/sd/www/node_config.txt')
                print("Node config is now on SD card")
            except:
                copy('/flash/node_config.txt', '/sd/www/node_config.txt')
                print("Node config is now on SD card")

        # try:
        #     print("Check Pymesh Config status")
        #     f = open('/sd/www/pymesh_config.json', 'r')
        #     f.close()
        #     print("Pymesh Config is on SD Card")
        #
        #
        # except:
        #         copy('/flash/pymesh_config.json', '/sd/www/pymesh_config.json')
        #         print("Pymesh config is now on SD card")

        try:
            print("Check Leader Mesh list status")
            f = open('/sd/www/leader_mesh_list.txt', 'r')
            f.close()
            print("Leader Mesh list is on SD Card")

        except:
            copy('/flash/lib/leader_mesh_list.txt', '/sd/www/leader_mesh_list.txt')
            print("Leader Mesh list is now on SD card")

        try:
            f = open('/sd/www/sms.txt', 'r')
            print("Already a SMS log, trimmed to last 100 SMSs")
            sms = f.readlines()
            f.close()
            os.remove('/sd/www/sms.txt')
            n = open('/sd/www/sms.txt', 'w+')
            for i in sms[-50:]:
                n.write(i)
            n.close()
        except:
            try:
                os.mkdir('/sd/www')
                f = open('/sd/www/sms.txt', 'w+')
                f.write("SMS log:\n")
            except:
                f = open('/sd/www/sms.txt', 'w+')
                f.write("SMS log:\n")
            print("SMS Log created")
        f.close()

    except:
        print("SD card not loaded, chat not saved")

def copy(s, t):
    try:
        f = open(t, 'rb')
    except:
        f = open(t, 'wb')
    s = open(s, "rb")
    while True:
        b = s.read(4096)
        print(b)
        if not b:
           break
        f.write(b)
    f.close()
    s.close()
