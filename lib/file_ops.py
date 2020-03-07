import os
from machine import SD

def sd_setup():
    try:
        sd = SD()
        os.mount(sd, '/sd')
        print("SD card mounted")
        # try:
        #     os.remove('/sd/www/chat.txt')
        # except:
        #     print('did not delete')
        try:
            f = open('/sd/www/status_log.txt', 'r')
            print("Already a status log")
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
            print("Already a chat log")
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
            print("check house status")
            f = open('/sd/lib/houses.txt', 'r')
            print("House list is on SD Card")
            c = open('/flash/lib/houses.txt', 'r')
            count_of_f = len(f.read())
            count_of_c = len(c.read())
            f.close()
            c.close()
            print("Check if House List has changed")
            if count_of_c > count_of_f:
                os.remove('/sd/lib/houses.txt')
                copy('/flash/lib/houses.txt', '/sd/lib/houses.txt')
                print("Updated House List from flash to SD")
            elif count_of_c < count_of_f:
                os.remove('/flash/lib/houses.txt')
                copy('/sd/lib/houses.txt', '/flash/lib/houses.txt')
                print("Updated House List from SD to flash")
            else:
                print("No changes made to house list.")

        except:
            try:
                os.mkdir('/sd/lib')
                copy('/flash/lib/houses.txt', '/sd/lib/houses.txt')
                print("House List now on SD card")
            except:
                copy('/flash/lib/houses.txt', '/sd/lib/houses.txt')
                print("House List now on SD card")

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
