# pymesh_microwebsrv2_chat
A hacky smash up of Pycom Pymesh from the frozen libaries and MicroWebSrv2 to create a local chat service on Lora.
I couldn't find a current example of how this worked (and I'm a slacker python coder that needs examples) so after getting it running,
figured it should be posted.

Doc to get started, though will need some updates.

See https://docs.pycom.io/pymesh/licence/ for requesting pymesh firmware.

Credit to Pycom and MicroWebSrv2 https://github.com/jczic/MicroWebSrv2 for a solid 95% of this.

Parts list per node:

Pycom Lopy4

Pycom Pytrack (or Pysense to save $10 but lose GPS)

Pycom IP67 case

Adafruit 2000ma 3.7v lithium battery

microSD card of some size, formatted

Micro USB to pcb pinout panel mount (find PN)

Right angle headers to squish and jam into the micro USB pcb (mostly as a hack for my lack of soldering skills) (adafruit)

right angle USB cable to be hacked so it fits in the case (no clearance from Pytrack usb to side of pycom case) (get Amazon link)

push pin-ie ish connectors to crimp onto hacked USB cable and push onto headers
12v IP67 switch from Amazon (get link)

JST connectors that actually fit into Pytrack and the adafruit battery. (link to adafruit)

u.sma to sma for Lora antenna (link)

905 mhz antenna (link)


bonus parts;
u.sma to sma for wifi antenna (link)

2.4 ghz wifi antenna (link)

thin foam to squish between parts

double sided sticky tape to tape battery to lid


Software setup (ToDo: move all the things you need to change for your install to easier to find spots)
All this applies to a device in the US, anywhere else you'll have to do a bit of research for your area and change
the radio frequencies and regions as needed. Docs on https://docs.pycom.io/pymesh

Otherwise:
In main.py
on line 359
wlan = WLAN(mode=WLAN.AP, ssid="wifi", auth=(WLAN.WPA2, 'password'), channel=11, antenna=WLAN.INT_ANT)
change "wifi" and passwordto what you want your SSID and password to to be (leave them in quotes)
set the antenna=WLAN.INT_ANT to either that if you're using the internal antenna or antenna=WLAN.EXT_ANT for external.
On the next line change the IP address if you want to.
Just make sure line 376 mws2.BindAddress = ('192.168.1.1', 80) matches the IP address you entered above.

On line 206 def mac_to_house(mac): change/add the names and mac addresses of all the nodes you'd like to use.

Under www/index.html change as you like, just keep the link to get to the chat and log.

Follow instructions on Pycom to load firmware to pytrack and then lopy4, load this repo to lopy4 (probably from atom, again Pycom
for instructions), after it starts up use the repl to run the "mac" command and change the mac to match one the list items from main.py
line 206 "mac_to_house" TODO really, make this easier....

Give everything 60 seconds to load, the AP should have started by then, connect to the wifi ap, navigate to 192.168.1.1 (or whatever
you changed it too), and click through to the wshcat page. Give that 10 seconds or so to populate a list of nodes, it'll show a
"welcome" message and the nodes currently online. Message away!
The first message seems to typically wake up the nodes on the mesh but not go through. The second message will almost always get to
all nodes.

Anytime the node is online, even if it doesn't have a computer connected to it, all received messages will get logged to the SD card.
Follow the "Log" link on either page to view it. Refresh to see latest.

The "www" folder is cloned onto the SD and all webpages served from there. Couldn't figure out how to serve the pages from flash and
then serve the log from SD. Hack.

I'll add pics/instructions on how I built my nodes, but the parts list is a good start, most things are straight forward.

General Todo's;
clean out any files not needed for wshcat

there's some code that was my attempt to hack in a "mesh status" function, pull it all out

figure out a better way to "message all"
  there's a multicast IP address in the mesh, but the pymesh.send_mess funtion only takes an MAC not an IP
  getting a signal message that goes to all IPs would be greatly preferred to the current "loop through all MACs that
  we think are currently connected" cuz....

often the mml command to list all nodes is out of date or doesn't work. You can message nodes from command line
not on the list, and get an ack, but they don't show up in mml.

setup a way to programmatically build the list of nodes/names and not have them hard coded.

ideally nuke bluetooth, the wifi/bt/gps/mesh pulls pretty solid power. battery life is at best 12 hours. Turning off
bt and gps adds hours of run time.

post details and code of the lora repeater only solar powered node built from a Mr Beams solar light. It still has issues,
if it runs out of juice, the node won't reconnect after the battery has recharged. But runs pretty solid if you have 8 hours of
sun a day. I don't.
